const axios = require('axios');

async function test() {
  const payload = {
    query: "How to reach Yadadri?",
    language: "en"
  };
  const activeConversationId = "b9dc0b9-48b0-4f74-bc73-ca535fa084fe";
  
  try {
    const targetUrl = 'http://127.0.0.1:8000/chat';
    const requestPayload = { ...payload, session_id: activeConversationId };
    
    console.log('Sending POST to', targetUrl);
    console.log('Payload:', requestPayload);
    
    const { data } = await axios.post(targetUrl, requestPayload, { timeout: 45_000 });
    console.log('Success!', data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.log('AXIOS ERROR:');
      console.log('Code:', error.code);
      console.log('Message:', error.message);
      if (error.response) {
        console.log('Status:', error.response.status);
        console.log('Data:', error.response.data);
      }
    } else {
      console.log('UNKNOWN ERROR:', error);
    }
  }
}
test();
