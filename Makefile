DOCKER_REGISTRY = dev.so.f-interop.eu:5000

build_image:
	docker build -t flora_test_application_server -f ./containers/test_application_server/Dockerfile .

build_sniffer:
	docker build -t flora_sniffer -f ./containers/packet_sniffer/Dockerfile .
	docker build -t flora_logger -f ./containers/logger/Dockerfile .

build_mock:
	docker build -t flora_test_application_server -f ./containers/test_application_server/Dockerfile .
	docker build -t flora_agent_mock -f ./containers/agent_mock/Dockerfile .

build_integration:
	docker build -t flora_logger -f ./containers/logger/Dockerfile .
	docker build -t flora_test_application_server -f ./containers/test_application_server/Dockerfile .
	docker build -t flora_agent_mock -f ./containers/agent_mock/Dockerfile .

upload_image:
	# Upload the testing tool
	docker tag flora_testing_app:latest $(DOCKER_REGISTRY)/flora_test_application_server:latest
	# We use direct IPv4 because IPv6 doesn't work at Inria Paris
	docker push $(DOCKER_REGISTRY)/flora_test_application_server:latest

	# Upload the agent
	docker tag flora_agent:latest $(DOCKER_REGISTRY)/flora_agent:latest
	# We use direct IPv4 because IPv6 doesn't work at Inria Paris
	docker push $(DOCKER_REGISTRY)/flora_agent:latest

	# Push to orchestrator
	ssh orchestrator 'docker pull $(DOCKER_REGISTRY)/flora_test_application_server:latest'
	ssh orchestrator 'docker tag $(DOCKER_REGISTRY)/flora_test_application_server:latest'
	ssh orchestrator 'docker pull $(DOCKER_REGISTRY)/flora_agent:latest'

docker_launch_test_application_server:
	docker run --rm --name flora_test_application_server --env-file env_var -p 5579:5579 -it flora_test_application_server supervisord -n -c supervisord.conf.ini

docker_launch_agent:
	docker run --rm --name flora_agent --privileged --env-file env_var -p 5008:5008 -it flora_agent supervisord -n -c supervisord.conf.ini

docker_launch_sniffer:
	docker run --rm --name flora_sniffer --privileged --env-file env_var -p 5007:5007 -it flora_sniffer

docker_launch_logger:
	docker run --rm --name flora_logger --privileged --env-file env_var -p 5003:5003 -it flora_logger

docker_launch_agent_mock:
	docker run --rm --name flora_agent_mock --privileged --env-file env_var -p 5008:5008 -it flora_agent_mock supervisord -n -c supervisord.conf.ini

docker_launch_mock_cli:
	docker run --env-file env_var -it flora_agent_mock bash

clean:
	docker system prune --all -y





