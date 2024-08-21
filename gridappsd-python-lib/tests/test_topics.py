from gridappsd import topics


# Correct topic strings are generated for given service, application, and simulation IDs
def test_correct_topic_strings():
    service_id = "dnp3"
    application_id = "app1"
    simulation_id = 12345

    assert topics.service_input_topic(
        service_id) == "/topic/goss.gridappsd.simulation.dnp3.input"
    assert topics.service_input_topic(
        service_id,
        simulation_id) == "/topic/goss.gridappsd.simulation.dnp3.12345.input"
    assert topics.service_output_topic(
        service_id) == "/topic/goss.gridappsd.simulation.dnp3.output"
    assert topics.service_output_topic(
        service_id,
        simulation_id) == "/topic/goss.gridappsd.simulation.dnp3.12345.output"
    assert topics.application_input_topic(
        application_id) == "/topic/goss.gridappsd.app1.input"
    assert topics.application_input_topic(
        application_id,
        simulation_id) == "/topic/goss.gridappsd.simulation.app1.12345.input"
    assert topics.application_output_topic(
        application_id) == "/topic/goss.gridappsd.app1.output"
    assert topics.application_output_topic(
        application_id,
        simulation_id) == "/topic/goss.gridappsd.simulation.app1.12345.output"
    assert topics.simulation_output_topic(
        simulation_id) == "/topic/goss.gridappsd.simulation.output.12345"
    assert topics.simulation_input_topic(
        simulation_id) == "/topic/goss.gridappsd.simulation.input.12345"


def test_handling_none_values():
    service_id = "dnp3"
    application_id = "app1"

    assert topics.service_input_topic(
        service_id, None) == "/topic/goss.gridappsd.simulation.dnp3.input"
    assert topics.service_output_topic(
        service_id, None) == "/topic/goss.gridappsd.simulation.dnp3.output"
    assert topics.application_input_topic(
        application_id, None) == "/topic/goss.gridappsd.app1.input"
    assert topics.application_output_topic(
        application_id, None) == "/topic/goss.gridappsd.app1.output"


def test_service_input_topic_without_simulation_id():
    service_id = "dnp3"
    simulation_id = None
    expected_topic = "/topic/goss.gridappsd.simulation.dnp3.input"
    result = topics.service_input_topic(service_id, simulation_id)
    assert result == expected_topic


def test_service_input_topic_with_simulation_id():
    service_id = "dnp3"
    simulation_id = 1234
    expected_topic = "/topic/goss.gridappsd.simulation.dnp3.1234.input"
    result = topics.service_input_topic(service_id, simulation_id)
    assert result == expected_topic
