#!/usr/bin/env python3
from export_data_by_measurement import round_down_to_microseconds
from datetime import datetime
import unittest


class ExporterTestCase(unittest.TestCase):

    def test_truncate_timestamp_to_microseconds(self):
        ts = round_down_to_microseconds("2021-01-03T10:32:20.123456789Z")
        self.assertEqual(ts, "2021-01-03T10:32:20.123456Z")
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")

        ts = round_down_to_microseconds("2021-01-03T10:32:20.123456Z")
        self.assertEqual(ts, "2021-01-03T10:32:20.123456Z")
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")

        ts = round_down_to_microseconds("2021-01-03T10:32:20.123Z")
        self.assertEqual(ts, "2021-01-03T10:32:20.123Z")
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")


if __name__ == "__main__":
    unittest.main()
