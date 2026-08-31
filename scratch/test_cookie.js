const axios = require('axios');
const jwt = require('jsonwebtoken');

const token = jwt.sign(
  { googleId: '123', email: 'test@example.com', name: 'Test' },
  'replace-this-with-a-long-random-string',
  { expiresIn: '7d' }
);

async function test() {
  try {
    console.log('Token:', token);
    const { data } = await axios.post('http://127.0.0.1:3000/api/chat', {
      query: "How to reach Yadadri?",
      language: "en"
    }, {
      headers: {
        Cookie: `pilgrim_session=${token}`
      }
    });
    console.log('Success!', data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.log('Failed:', error.response?.status, error.response?.data);
    } else {
      console.log('Failed:', error);
    }
  }
}
test();
