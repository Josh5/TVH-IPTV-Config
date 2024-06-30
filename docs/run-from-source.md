# Run from source

## Clone project

Clone this project somewhere
```
git clone https://github.com/Josh5/TVH-IPTV-Config.git
cd TVH-IPTV-Config
```

## Run the build scripts

1) Run the setup script. This will create a local environment, installing a Python virtual environment and all dependencies listed in the requirements.txt file, along with the building the frontend. You should re-run this script whenever you pull updates from GitHub.
```
./devops/setup_local_dev_env.sh
```
2) Run the project.
```
source venv-local/bin/activate
python3 ./run.py
```

This will create a directory within this project root called `./dev_env` which contains all configuration and cache data.

## Update project

Pull updates
```
git pull origin master
```

Rebuild
```
./devops/setup_local_dev_env.sh
./devops/run_local_dev_env.sh
```
