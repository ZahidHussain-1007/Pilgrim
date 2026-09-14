const jwt = require('jsonwebtoken');
const axios = require('axios');

async function test() {
  const secret = 'replace-this-with-a-long-random-string';
  const payload = {
    googleId: '117395626089233632445',
    email: 'trivikram.vikrala@gmail.com',
    name: 'Trivikram Vikrala'
  };
  const token = jwt.sign(payload, secret, { expiresIn: '7d' });
  const cookie = `pilgrim_session=${token}`;
  
  try {
    const res = await axios.post('http://localhost:3000/api/chat', {
      query: 'Tell me about Yadadri.',
      temple: 'yadadri',
      language: 'en',
      conversationId: null
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Cookie': cookie
      }
    });
    console.log("Success:", res.data);
  } catch (err) {
    if (err.response) {
      console.log("Error status:", err.response.status);
      console.log("Error data:", err.response.data);
    } else {
      console.log("Error:", err.message);
    }
  }
}

test();
