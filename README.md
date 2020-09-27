# Twitter Count API

## Installation
1. Install [virtualenv](https://virtualenv.pypa.io/en/latest/index.html)
2. Set a new environment:
```
virtualenv venv
```
3. Activate environment:
```
source ./venv/bin/activate
```
4. Clone this repo

## Development
1. Activate virtualenv:
```
source ./venv/bin/activate
```
2. Access the repo folder:
```
cd ./twitter-count-api
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Install Serverless Python Requirements plugin:
```
npm install
```

## How to run the cli script
`src.cli` package executes the script used for counting the tweets using a given query and optional date range arguments. **query** argument is mandatory, however, **from** and **to** dates are optional. You can execute the script in two ways:
Providing the **query** argument only. This will fetch the count for the last 31 days by default.

**Usage**:
```
python -m src.cli <query>
```
**Example**:
```
python -m src.cli 'profile_country:ES (COVID19)'
```
Providing the **query** and **from** and **to** arguments.

**Usage**:
```
python -m src.cli <query> <from> <to>
```
**Example**:
```
python -m src.cli 'profile_country:ES (COVID19)' 2020-04-30 2020-05-31
```

## Setting environment variables
1. Create **.env** file in **twitter-counter-api/src** directory.
2. Usage .env.example as a reference.
3. To add a new variable, follow this pattern:
```
VARIABLE_NAME="VARIABLE_VALUE"
```
4. Importing **settings.py** automatically loads the variables defined in **.env** file.

## Running unit tests
1. All unit tests should be placed in tests directory/package in any module.
2. The following command will auto-discover all unit tests and execute them.
```
python -m unittest
```