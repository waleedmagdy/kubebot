from flask import Flask, Response, request, jsonify
from slackeventsapi import SlackEventAdapter
import os
import subprocess
import json
from threading import Thread
from slack import WebClient

app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
slack_token = os.environ['SLACK_BOT_TOKEN']
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']

slack_client = WebClient(slack_token)

slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app
)

available_commands = ["get", "describe", "logs"]
available_sub_commands = {
    "get": ["pods", "nodes", "services"],
    "describe": ["pods", "nodes", "services"],
    "logs": ["pods"]
}

selected_actions = {}

def get_available_namespaces():
    try:
        command = ["kubectl", "get", "namespaces", "-o", "jsonpath='{.items[*].metadata.name}'"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        namespaces = result.stdout.strip("'").split()
        return namespaces
    except subprocess.CalledProcessError as e:
        print("Error running kubectl command:", e)
        return []

def get_available_pods(namespace):
    try:
        command = ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath='{.items[*].metadata.name}'"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pods = result.stdout.strip("'").split()
        return pods
    except subprocess.CalledProcessError as e:
        print("Error running kubectl command:", e)
        return []

def run_kubectl_command(channel_id, command):
    try:
        print(f"Running command: {command}")  
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.output}\n```")

@slack_events_adapter.on("app_mention")
def handle_mention(event_data):
    def send_kubectl_options(value):
        event_data = value
        message = event_data["event"]
        if message.get("subtype") is None:
            channel_id = message["channel"]
            user_id = message["user"]

            response_message = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hello <@{user_id}>! Please select a kubectl command:"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a command"
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": command
                                        },
                                        "value": command
                                    }
                                    for command in available_commands
                                ],
                                "action_id": "kubectl_command_select"
                            }
                        ]
                    }
                ]
            }

            slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])

    thread = Thread(target=send_kubectl_options, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)

@app.route("/interactions", methods=["POST"])
def handle_interactions():
    payload = json.loads(request.form.get("payload"))
    channel_id = payload["channel"]["id"]
    user_id = payload["user"]["id"]
    action_id = payload["actions"][0]["action_id"]

    if action_id == "kubectl_command_select":
        selected_command = payload["actions"][0]["selected_option"]["value"]
        selected_actions[channel_id] = {"command": selected_command}
        sub_command_menu = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Please select a sub-command:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a sub-command"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": sub_command
                                    },
                                    "value": sub_command
                                }
                                for sub_command in available_sub_commands.get(selected_command, [])
                            ],
                            "action_id": "kubectl_sub_command_select"
                        }
                    ]
                }
            ]
        }
        slack_client.chat_postMessage(channel=channel_id, blocks=sub_command_menu["blocks"])

    elif action_id == "kubectl_sub_command_select":
        selected_sub_command = payload["actions"][0]["selected_option"]["value"]
        if channel_id in selected_actions:
            selected_actions[channel_id]["sub_command"] = selected_sub_command
        available_namespaces = get_available_namespaces()
        namespaces_menu = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Please select a namespace:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a namespace"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": namespace
                                    },
                                    "value": namespace
                                }
                                for namespace in available_namespaces
                            ],
                            "action_id": "kubectl_namespace_select"
                        }
                    ]
                }
            ]
        }
        slack_client.chat_postMessage(channel=channel_id, blocks=namespaces_menu["blocks"])

    elif action_id == "kubectl_namespace_select":
        selected_namespace = payload["actions"][0]["selected_option"]["value"]
        if channel_id in selected_actions:
            selected_actions[channel_id]["namespace"] = selected_namespace

        selected_command = selected_actions.get(channel_id, {}).get("command", "get")
        selected_sub_command = selected_actions.get(channel_id, {}).get("sub_command", "nodes")

        if selected_sub_command == "pods" and selected_command in ["describe", "logs"]:
            available_pods = get_available_pods(selected_namespace)
            pods_menu = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Please select a pod:"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a pod"
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": pod
                                        },
                                        "value": pod
                                    }
                                    for pod in available_pods
                                ],
                                "action_id": "kubectl_pod_select"
                            }
                        ]
                    }
                ]
            }
            slack_client.chat_postMessage(channel=channel_id, blocks=pods_menu["blocks"])
        else:
            command = f"kubectl {selected_command} {selected_sub_command} -n {selected_namespace}"
            run_kubectl_command(channel_id, command)

    elif action_id == "kubectl_pod_select":
        selected_pod = payload["actions"][0]["selected_option"]["value"]
        selected_namespace = selected_actions.get(channel_id, {}).get("namespace", "")
        selected_command = selected_actions.get(channel_id, {}).get("command", "describe")

        if selected_namespace:  # Ensure namespace is not empty
            if selected_command in ["logs", "describe"]:
                command = f"kubectl {selected_command} {selected_pod} -n {selected_namespace}"  # Removed the word "pod"
            else:
                command = f"kubectl {selected_command} pod {selected_pod} -n {selected_namespace}"
            run_kubectl_command(channel_id, command)
        else:
            slack_client.chat_postMessage(channel=channel_id, text="Namespace not selected. Please start over.")

    return Response(status=200)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
