#!/usr/bin/env python

# Copyright 2016 Jason Horne
# Copyright 2017 Chris Gheen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import logging
import sys
import pycarwings2
import pytest

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

def test_bad_password():
	with pytest.raises(pycarwings2.CarwingsError) as excinfo:
		s =  pycarwings2.Session("user@domain.com", "password", "NE")
		l = s.get_leaf()
	assert 'INVALID' in str(excinfo.value)

