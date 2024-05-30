import unittest
import lambda_function


class TestHandlerCase(unittest.TestCase):

    def test_response(self):
        print("testing response.")
        event={'city':'Vancouver'}
        result = lambda_function.lambda_handler(event, None)
        print(result)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        self.assertIn('city :'+event['city'], result['body'])
        self.assertIn('current_temperature :', result['body'])

if __name__ == '__main__':
    unittest.main()
