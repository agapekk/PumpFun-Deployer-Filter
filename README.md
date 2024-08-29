# Deployer Filter v1.0.3

## Overview

This script filters deployers (creators) on Pump.fun based on their previous token creation history, market cap, and completion ratio. The script reads a list of deployer addresses from a file, checks their past deployments, and filters them based on user-defined criteria such as market cap and the success rate of their tokens.

## Features

- **Deployer Filtering**: Filters deployers based on their previous tokens' market cap and completion ratio.
- **Exclusion of Certain Tokens**: Automatically excludes tokens with certain keywords (e.g., "TEST", "RUG", "BOT") from consideration.
- **Proxy Support**: Allows the use of an HTTP proxy to fetch data.
- **Concurrency**: Utilizes multithreading to speed up the processing of deployer addresses.
- **Customizable Filtering Criteria**:
  - Minimum market cap for at least one of a deployer’s previous tokens.
  - Option to filter only deployers whose tokens have completed.
  - Completion ratio threshold.

## Prerequisites

- Python 3.x
- Required Python libraries:
  - `requests`
  - `json`
  - `re`
  - `time`
  - `rich`
  - `concurrent.futures`
  - `datetime`
  - `os`
  - `fade`

You can install the required libraries using `pip`:

```bash
pip install requests rich fade
