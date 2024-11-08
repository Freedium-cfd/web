from datetime import datetime
from typing import Optional, Union

import pendulum


class DateTimeUtils:
    @staticmethod
    def to_milliseconds(
        dt_input: Optional[Union[str, datetime]] = None, tz: str = "UTC"
    ) -> int:
        """
        Convert input to milliseconds with timezone support.

        Args:
            dt_input: String, datetime, or None for current time
            tz: Timezone string (default: 'UTC')

        Returns:
            Timestamp in milliseconds
        """
        try:
            if dt_input is None:
                return pendulum.now(tz).int_timestamp * 1000

            if isinstance(dt_input, str):
                dt = pendulum.parse(dt_input, tz=tz)
            else:
                dt = pendulum.instance(dt_input).in_timezone(tz)

            return dt.int_timestamp * 1000

        except Exception as e:
            raise ValueError(f"Invalid datetime input: {e}")  # type: NoReturn
