import json
import lorawan.flora_agent.messenger.generator as gen


def agent_mock_main():
    with open('testing_tool_conf.json') as json_file:
        text = json_file.read()
        test_config_json = json.loads(text)

    generator = gen.MessageGenerator(config_dev_dict=test_config_json["Device"],
                                     conf_testserver_dict=test_config_json["AppServer"])
    print("\n\nAgent mock started and ready to interact with the Testing App Server.", flush=True)
    print("Use de command line interface to interact with the mock.", flush=True)
    generator.start_consuming()


if __name__ == '__main__':
    agent_mock_main()

