import pytest

from card_automation_server.workers.events import RawCommServerMessage, MessageParseException


class TestRawCommServerMessageParsing:
    def test_can_parse_all_integers(self):
        message = RawCommServerMessage.parse("1 2 3 4")

        assert isinstance(message, RawCommServerMessage)
        assert message.data == [1, 2, 3, 4]
        assert message.type == 1

    def test_can_parse_with_string_message(self):
        message = RawCommServerMessage.parse("1 2 3 4 *test")

        assert isinstance(message, RawCommServerMessage)
        assert message.data == [1, 2, 3, 4, "test"]
        assert message.type == 1

    def test_parse_with_empty_string_fails(self):
        with pytest.raises(MessageParseException):
            RawCommServerMessage.parse("")

    def test_parsing_only_text_fails(self):
        with pytest.raises(MessageParseException):
            RawCommServerMessage.parse("*test")

    def test_parsing_ignores_newlines(self):
        message = RawCommServerMessage.parse("1 2 3 4 *test\r\n")

        assert isinstance(message, RawCommServerMessage)
        assert message.data == [1, 2, 3, 4, "test"]
        assert message.type == 1

    def test_parsing_with_multiple_asterisks(self):
        message = RawCommServerMessage.parse("1 2 3 4 *test *this*\r\n")

        assert isinstance(message, RawCommServerMessage)
        assert message.data == [1, 2, 3, 4, "test *this*"]
        assert message.type == 1