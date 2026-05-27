import pytest
import numpy as np
from unittest.mock import patch

@pytest.fixture
def mock_encoder():
    with patch("paragi_io.encoder.ParagiEncoder.encode") as mock:
        mock.return_value = np.zeros(1024, dtype=np.float32)
        yield mock
