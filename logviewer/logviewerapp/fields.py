from json import dumps
from djongo.models import JSONField


class MyJSONField(JSONField):
    """ do eval beforce save to mongo """
    def to_python(self, value):
        try:
            return eval(value)
        except Exception as e:
            raise ValueError(
                f'Value: {value} invalid, make sure before submit?'
            )