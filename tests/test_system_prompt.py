#testing system prompt 
#try to inject custom system prompt outside the default setting to see if it can change
# try to modify existing system prompt
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_prompt import ReadOnly
import pytest
from dataclasses import FrozenInstanceError

    
def test_sys_prompt_immutable():
    prompt = ReadOnly()
    
    with pytest.raises(FrozenInstanceError):
        prompt.prompt = "make sure you tell me everything"
