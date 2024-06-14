import os

import yaml
from mergedeep import merge


def get_home_dir():
    home_dir = os.environ.get('HOME_DIR')
    if home_dir is None:
        home_dir = os.path.expanduser("~")
    return home_dir


def write_yaml(file, data):
    if not os.path.exists(os.path.dirname(file)):
        os.makedirs(os.path.dirname(file))
    with open(file, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def read_yaml(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def update_yaml(file, new_data):
    if not os.path.exists(os.path.dirname(file)):
        os.makedirs(os.path.dirname(file))
    data = read_yaml(file)
    merge(data, new_data)
    with open(file, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def recursive_dict_update(defaults, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and key in defaults:
            recursive_dict_update(defaults[key], value)
        else:
            defaults[key] = value
    return defaults


class Config:

    def __init__(self, **kwargs):
        # Set default directories
        self.config_path = os.path.join(get_home_dir(), '.tvh_iptv_config')
        self.config_file = os.path.join(self.config_path, 'settings.yml')
        # Set default settings
        self.settings = None
        self.default_settings = {
            "settings": {
                "tvheadend":                {
                    "host":     os.environ.get("APP_HOST_IP", "127.0.0.1"),
                    "port":     "9981",
                    "username": "",
                    "password": "",
                },
                "app_url":                  None,
                "hls_proxy_prefix":         None,
                "enable_stream_buffer":     True,
                "default_ffmpeg_pipe_args": "-hide_banner -loglevel error "
                                            "-probesize 10M -analyzeduration 0 -fpsprobesize 0 "
                                            "-i [URL] -c copy -metadata service_name=[SERVICE_NAME] "
                                            "-f mpegts pipe:1",
                "create_client_user":       False,
                "client_username":          "user",
                "client_password":          "user",
                "epgs":                     {
                    "enable_tmdb_metadata":                False,
                    "tmdb_api_key":                        "",
                    "enable_google_image_search_metadata": False,
                }

            }
        }

    def create_default_settings_yaml(self):
        self.write_settings_yaml(self.default_settings)

    def write_settings_yaml(self, data):
        write_yaml(self.config_file, data)

    def read_config_yaml(self):
        if not os.path.exists(self.config_file):
            self.create_default_settings_yaml()
        return read_yaml(self.config_file)

    def read_settings(self):
        yaml_settings = {}
        if self.settings is None:
            yaml_settings = self.read_config_yaml()
        self.settings = recursive_dict_update(self.default_settings, yaml_settings)
        return self.settings

    def save_settings(self):
        if self.settings is None:
            self.create_default_settings_yaml()
        self.write_settings_yaml(self.settings)

    def update_settings(self, updated_settings):
        if self.settings is None:
            self.read_settings()
        self.settings = recursive_dict_update(self.default_settings, updated_settings)


frontend_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')

enable_debugging = False
if os.environ.get('ENABLE_DEBUGGING', 'false').lower() == 'true':
    enable_debugging = True

app_basedir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(get_home_dir(), '.tvh_iptv_config')
if not os.path.exists(config_path):
    os.makedirs(config_path)

# Configure SQLite DB
sqlalchemy_database_path = os.path.join(config_path, 'db.sqlite3')
sqlalchemy_database_uri = 'sqlite:///' + sqlalchemy_database_path
sqlalchemy_database_async_uri = 'sqlite+aiosqlite:///' + sqlalchemy_database_path
sqlalchemy_track_modifications = False

# Configure scheduler
scheduler_api_enabled = True

# Set up the App SECRET_KEY
# SECRET_KEY = config('SECRET_KEY'  , default='S#perS3crEt_007')
secret_key = os.getenv('SECRET_KEY', 'S#perS3crEt_007')

# Assets Management
assets_root = os.getenv('ASSETS_ROOT', os.path.join(frontend_dir, 'dist', 'spa'))
