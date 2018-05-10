DEFAULT_FNCS_LOCATION = 'tcp://localhost:5570'
FNCS_BASE_INPUT_TOPIC = '/topic/goss.gridappsd.simulation.input'
FNCS_BASE_OUTPUT_TOPIC = '/topic/goss.gridappsd.simulation.output'
BASE_SIMULATION_STATUS_TOPIC = "/topic/goss.gridappsd.process.log.simulation"

BLAZEGRAPH = "/queue/goss.gridappsd.process.request.data.powergridmodel"
LOGS = "/queue/goss.gridappsd.process.request.logs"
TIMESERIES = "/queue/goss.gridappsd.process.request.timeseries"

CONFIG = "/queue/goss.gridappsd.process.request.config"
PLATFORM_STATUS = "/queue/goss.gridappsd.process.request.status.platform"

BASE_TOPIC_PREFIX = "goss.gridappsd"
PROCESS_PREFIX = ".".join((BASE_TOPIC_PREFIX, "process"))
REQUEST_PLATFORM_STATUS = ".".join([PROCESS_PREFIX, "request.status.platform"])

REQUEST_DATA = ".".join((PROCESS_PREFIX, "request.data"))
REQUEST_SIMULATION_STATUS = ".".join((PROCESS_PREFIX, "request.status.simulation"))

REQUEST_POWERGRID_DATA = ".".join((REQUEST_DATA, "powergridmodel"))


def fncs_input_topic(simulation_id):
    return "{}.{}".format(FNCS_BASE_INPUT_TOPIC, simulation_id)


def fncs_output_topic(simulation_id):
    return "{}.{}".format(FNCS_BASE_OUTPUT_TOPIC, simulation_id)

"""
//topics
	public static final String topic_prefix = "goss.gridappsd";
	
	//Process Manager topics
	public static final String topic_process_prefix = topic_prefix+".process";
	public static final String topic_request = topic_prefix+".process";
	
	
	
	//Process Manager Request Topics
	public static final String topic_requestSimulation = topic_process_prefix+".request.simulation";
	public static final String topic_requestData = topic_process_prefix+".request.data";
	public static final String topic_requestConfig = topic_process_prefix+".request.config";
	public static final String topic_requestApp = topic_process_prefix+".request.app";
	public static final String topic_requestSimulationStatus = topic_process_prefix+".request.status.simulation";
	public static final String topic_requestPlatformStatus = topic_process_prefix+".request.status.platform";
	
	
	public static final String topic_requestListAppsWithInstances = "goss.gridappsd.process.request.list.apps";
	public static final String topic_requestListServicesWithInstances = "goss.gridappsd.process.request.list.services";
	
	public static final String topic_responseData = topic_prefix+".response.data";
	
	public static final String topic_platformLog = topic_prefix+".platform.log";
	
	//App Request Topics
	public static final String topic_app_register = topic_requestApp+".register";
	public static final String topic_app_list = topic_requestApp+".list";
	public static final String topic_app_get = topic_requestApp+".get";
	public static final String topic_app_deregister = topic_requestApp+".deregister";
	public static final String topic_app_start = topic_requestApp+".start";
	public static final String topic_app_stop = topic_requestApp+".stop";
	public static final String topic_app_stop_instance = topic_requestApp+".stopinstance";
	
	
	//Configuration Manager topics
	public static final String topic_configuration = topic_prefix+".configuration";
	public static final String topic_configuration_powergrid = topic_configuration+".powergrid";
	public static final String topic_configuration_simulation = topic_configuration+".simulation";
	
	//Simulation Topics
	public static final String topic_simulation = topic_prefix+".simulation";
	public static final String topic_simulationInput = topic_simulation+".input";
	public static final String topic_simulationOutput = topic_simulation+".output";
	public static final String topic_simulationLog = topic_simulation+".log.";
	
	//Service Topics
	public static final String topic_service = topic_prefix+".simulation";
	public static final String topic_serviceInput = topic_service+".input";
	public static final String topic_serviceOutput = topic_service+".output";
	public static final String topic_serviceLog = topic_service+".log";
		
	//Application Topics
	public static final String topic_application = topic_prefix+".simulation";
	public static final String topic_applicationInput = topic_application+".input";
	public static final String topic_applicationOutput = topic_application+".output";
    public static final String topic_applicationLog = topic_application+".log";
"""