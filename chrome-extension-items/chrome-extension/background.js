chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'generateSchedule') {
    const { calendarContent, healthContent } = request;

    fetch('http://localhost:5000/generate_schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        calendarContent,
        healthContent,
        date: new Date().toISOString()
      })
    })
    .then(response => response.json())
    .then(schedule => {
      sendResponse({ success: true, schedule });
    })
    .catch(error => {
      console.error('Error:', error);
      sendResponse({ success: false, message: 'Failed to generate schedule', error: error.toString() });
    });

    // Keep the message channel open for async `sendResponse`
    return true;
  }
});
