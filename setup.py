"""Used to set secret variables, like the token, when using the Dockerfile"""
import sys
import argparse
import yaml


def create_argparser() -> argparse.ArgumentParser:
    """Generates the appropriate argparser

    Returns:
        the argparser used to parse the arguments
    """
    parser = argparse.ArgumentParser(description="Settings utility to edit the config/settings.yaml file", allow_abbrev=True)
    parser.add_argument('token', help="the token of your telegram bot")
    parser.add_argument('--test_api_hash', help="hash of the telegram app used for testing")
    parser.add_argument('--test_api_id', type=int, help="id of the telegram app used for testing")
    parser.add_argument('--test_session', help="session of the telegram app used for testing")
    parser.add_argument('--test_tag', help="tag of the telegram bot used for testing. Include the '@' character")
    parser.add_argument('--test_token', help="token for the telegram bot used for testing")
    parser.add_argument('--test_representatives_group', help="id of the representatives group used for testing")
    parser.add_argument('--test_dev_group_chatid', help="id of the representatives group used for testing")
    parser.add_argument('-p', '--path', help="path of the setting file (default: %(default)s)", default="config/settings.yaml")
    return parser


def main():
    """Main function"""
    parser = create_argparser()
    args = vars(parser.parse_args())

    try:
        with open(args['path'], "r", encoding="UTF-8") as yaml_file:
            config_map = yaml.safe_load(yaml_file)
    except FileNotFoundError as error:
        print(error)
        sys.exit(2)

    config_map['token'] = args['token']
    config_map['test']['api_id'] = args['test_api_id']
    config_map['test']['api_hash'] = args['test_api_hash']
    config_map['test']['session'] = args['test_session']
    config_map['test']['tag'] = args['test_tag']
    config_map['test']['token'] = args['test_token']
    config_map['test']['representatives_group'] = args['test_representatives_group']
    config_map['test']['dev_group_chatid'] = args['test_dev_group_chatid']

    with open(args['path'], "w", encoding='UTF-8') as yaml_file:
        yaml.dump(config_map, yaml_file)


if __name__ == "__main__":
    main()
