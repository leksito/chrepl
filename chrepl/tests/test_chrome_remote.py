from mock import Mock
import pytest

from chrepl.chrome_remote import EventHandler

@pytest.fixture(scope='function')
def events_mock(request):
    events = Mock()
    events.get = Mock(return_value={'method': 'Called.method', 'params': {'params1': 1}})
    events.put = Mock(return_value={'method': 'Called.method', 'params': {'params1': 1}})
    return events

@pytest.fixture(scope='function')
def event_handlers_mock(request):
    return {
        'Called.method': Mock(),
        'NotCalled.method': Mock()
    }

@pytest.fixture(scope='function')
def stopped_mock(request):
    stopped = Mock()
    stopped.is_set.side_effect = [False, True]
    return stopped
    
def test_event_handler(events_mock, event_handlers_mock, stopped_mock):
    EventHandler(events_mock, event_handlers_mock, stopped_mock).run()
    event_handlers_mock['Called.method'].assert_called_once_with(params1=1)
    event_handlers_mock['NotCalled.method'].assert_not_called()

def test_receive_loop_process_message():
    pass

