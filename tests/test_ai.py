import pytest

def test_function_calling():
    processor = AvitoAIProcessor()
    message = "2 грузчика на 3 часа, телефон +79991234567"
    
    response = processor.process_with_functions(
        message=message,
        chat_id="test_123"
    )
    
    assert "сделка" in response.lower()