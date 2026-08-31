const axios = require('axios');

async function test() {
  try {
    const payload = {
      query: "How to reach Yadadri?",
      temple: "",
      language: "en"
    };
    const activeConversationId = "test1234-abcd-5678-efgh-1234567890ab";
    
    console.log("Sending request to FastAPI...");
    const { data } = await axios.post(`http://127.0.0.1:8000/chat`, {
      ...payload,
      session_id: activeConversationId
    }, { timeout: 45_000 });
    console.log("Success:", data);
  } catch (error) {
    console.log("FASTAPI REQUEST FAILED:");
    if (axios.isAxiosError(error)) {
      console.log('Message:', error.message);
      console.log('Code:', error.code);
      console.log('Response Status:', error.response?.status);
      console.log('Response Data:', error.response?.data);
    } else {
      console.log('Error:', error);
    }
  }
}
test();
