# Slack Kubernetes Bot

This Slack bot is built using Python and Flask and is designed to interact with a Kubernetes cluster via `kubectl` commands. Users can invoke the bot in Slack to perform various Kubernetes operations like getting information about pods, nodes, services, etc.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- Kubernetes cluster management via Slack
- Available Commands:
  - `get`: Retrieve information about pods, nodes, and services
  - `describe`: Detailed information about pods, nodes, and services
  - `logs`: View logs of pods

## Prerequisites

- Python 3.x
- pip
- Kubernetes cluster
- Slack workspace

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/waleedmagdy/kubebot
    ```
2. Navigate into the project directory:
    ```bash
    cd kubebot
    ```

## Environment Variables

You need to set the following environment variables for the app to function correctly:

- `SLACK_SIGNING_SECRET`: Your Slack signing secret
- `SLACK_BOT_TOKEN`: Your Slack bot user token
- `VERIFICATION_TOKEN`: Your Slack verification token

You can either set these in your shell environment, or store them in a `.env` file at the root of your project. If you choose the latter, make sure to load them in your application.

## Running the App

1. Start the Flask application:
    ```bash
    python bot.py
    ```
2. The application will start on port 3000 by default. You can visit `http://localhost:3000` to make sure it's running.

## Usage

1. Invite the bot to a channel or mention it using `@BotName`.
2. Follow the interactive messages to execute Kubernetes commands.

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
