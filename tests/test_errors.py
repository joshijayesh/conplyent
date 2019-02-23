from unittest import TestCase, main

import conplyent


class TestConnectionError(TestCase):
    def test_connection_error(self):
        connection = conplyent.client.add("localhost")
        with self.assertRaises(ConnectionError) as context:
            connection.connect(timeout=0.25)
        self.assertTrue("Server not responding" in str(context.exception))


if(__name__ == "__main__"):
    main()
