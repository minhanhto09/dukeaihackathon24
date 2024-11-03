from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from datetime import datetime, timedelta
import pytz
import json
import os
import ics
from typing import Dict, List, Optional
from config import commercial_llm_name, temperature
from dotenv import load_dotenv
load_dotenv()

class TaskTimeEstimator:
    def __init__(self, history_file: str = 'task_history.json'):
        self.history_file = history_file
        self.task_history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load historical task completion times"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                task_history = json.load(f)
        else:
            task_history = {}

        # Ensure all expected task types exist in the dictionary
        for task_type in ['homework', 'homework_due', 'exam_prep', 'exam', 'presentation', 'project']:
            if task_type not in task_history:
                task_history[task_type] = {}

        return task_history

    def _save_history(self):
        """Save updated task history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.task_history, f)
    
    def get_estimated_time(self, task_type: str, subject: str, user_estimate: float) -> float:
        """Get estimated time based on historical data and user input"""
        subject_history = self.task_history[task_type].get(subject, [])
        if not subject_history:
            return user_estimate
        
        # Calculate average actual time taken
        actual_times = [entry['actual_time'] for entry in subject_history[-5:]]  # Last 5 instances
        historical_avg = sum(actual_times) / len(actual_times)
        
        # Weight historical data vs user estimate
        if len(actual_times) >= 3:
            return (historical_avg * 0.7) + (user_estimate * 0.3)
        return (historical_avg * 0.3) + (user_estimate * 0.7)
    
    def update_task_time(self, task_type: str, subject: str, estimated_time: float, actual_time: float):
        """Update task history with actual completion time"""
        if task_type not in self.task_history:
            self.task_history[task_type] = {}
        
        if subject not in self.task_history[task_type]:
            self.task_history[task_type][subject] = []
        
        self.task_history[task_type][subject].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'estimated_time': estimated_time,
            'actual_time': actual_time
        })
        
        self._save_history()

class AcademicAdaptiveScheduler:
    def __init__(self):
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=commercial_llm_name,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature= temperature
        )
        
        self.time_estimator = TaskTimeEstimator()
        
        # Enhanced prompt template for academic scheduling
        self.schedule_prompt = PromptTemplate(
            input_variables=["calendar_events", "health_data", "deadlines", "task_estimates", "previous_completion", "constraints"],
            template="""
            Based on the following information:
            Calendar Events: {calendar_events}
            Academic Deadlines: {deadlines}
            Task Time Estimates: {task_estimates}
            Health Data: {health_data}
            Previous Task Completion Rate: {previous_completion}
            User Constraints: {constraints}
            
            Generate an optimized daily schedule for the week of November 3 to November 10 (for days without Health Data) without changing any existing time blocks in Calendar Events.

            The schedule should:

            1. Incorporate all existing fixed events.
            2. Add preparation time blocks specifically for homework and exams.
            3. Balance academic workload, informed by energy level patterns inferred from available Health Data.
            4. Include buffer time for tasks that typically require extra time.
            5. Adapt task timing to predicted energy levels from Health Data.
    

            For each task, provide:
            1. Recommended time slots.
            2. Expected duration based on historical data.
            3. Priority level.
            5. Alternative slots if the task takes longer than needed.
            
            Provide the schedule in JSON format with detailed time slots and task information.
            """
        )
        
        self.schedule_chain = LLMChain(llm=self.llm, prompt=self.schedule_prompt)
    
    def parse_ics_calendar(self, ics_file_path: str) -> List[Dict]:
        """Parse ICS file and extract academic events and deadlines"""
        with open(ics_file_path, 'r') as f:
            calendar = ics.Calendar(f.read())
        
        events = []
        for event in calendar.events:
            event_type = self._classify_academic_event(event.name)
            events.append({
                'name': event.name,
                'type': event_type,
                'start': event.begin.datetime.isoformat(),  # Convert to ISO string
                'end': event.end.datetime.isoformat(),      # Convert to ISO string
                'description': event.description,
                'is_deadline': event_type in ['homework_due', 'exam'] #, 'presentation']
            })
        print(f"Event: {event.name}, is_deadline: {event_type in ['homework_due', 'exam']}")
        return events

    
    def _classify_academic_event(self, event_name: str) -> str:
        """Classify event type based on name/description"""
        event_name = event_name.lower()
        if any(word in event_name for word in ['exam', 'test', 'quiz', 'final']): 
            return 'exam'
        elif any(word in event_name for word in ['homework', 'assignment']):
            return 'homework_due'
        elif any(word in event_name for word in ['presentation', 'project']):
            return 'presentation'
        elif any(word in event_name for word in ['class', 'lecture']):
            return 'class'
        return 'other'
    
    def get_task_time_estimate(self, task_type: str, subject: str) -> Dict:
        """Get time estimate for a task and prompt user for input"""
        print(f"\nEstimating time for {task_type} in {subject}")
        user_estimate = float(input(f"How many hours do you think you need for this {task_type}? "))
        
        historical_estimate = self.time_estimator.get_estimated_time(
            task_type, subject, user_estimate
        )
        
        return {
            'task_type': task_type,
            'subject': subject,
            'user_estimate': user_estimate,
            'historical_estimate': historical_estimate,
            'final_estimate': historical_estimate
        }
    
    def generate_schedule(self, ics_file_path: str, date: datetime, health_data: Dict, constraints: Optional[Dict] = None):
        """Generate an optimized schedule based on academic calendar"""
        # Parse calendar events
        calendar_events = self.parse_ics_calendar(ics_file_path)
        
        # Make start_of_week and end_of_week timezone-aware
        timezone = pytz.UTC
        start_of_week = timezone.localize(date - timedelta(days=date.weekday()))
        end_of_week = start_of_week + timedelta(days=6)
        
        # Convert event['start'] back to datetime for comparison
        deadlines = [
            event for event in calendar_events 
            if event['is_deadline'] and start_of_week <= datetime.fromisoformat(event['start']) <= end_of_week
        ]
        print("Deadlines for the week:", [event['name'] for event in deadlines])

        # Get time estimates for deadline tasks
        task_estimates = []
        for deadline in deadlines:
            estimate = self.get_task_time_estimate(
                deadline['type'],
                deadline['name'].split('-')[0].strip()  # Assuming format: "Subject - Assignment"
            )
            task_estimates.append(estimate)
        
        # Generate schedule using LLM
        schedule_response = self.schedule_chain.run({
            "calendar_events": json.dumps(calendar_events),
            "deadlines": json.dumps(deadlines),
            "task_estimates": json.dumps(task_estimates),
            "health_data": json.dumps(health_data),
            "previous_completion": json.dumps(self.time_estimator.task_history),
            "constraints": json.dumps(constraints if constraints else {})
        })
        
        # Debugging: print the raw response
        print("Schedule Response:", schedule_response)  # Print to check the content

        if not schedule_response:
            print("Error: The LLM returned an empty response.")
            return {}  # Or handle as appropriate
        try:
            return json.loads(schedule_response)
        except json.JSONDecodeError:
            print("Error: schedule_response is not valid JSON.")
            return {}  # Handle the error or return an empty dictionary

    def update_task_completion(self, task_type: str, subject: str, estimated_time: float, actual_time: float):
        """Update task completion history"""
        self.time_estimator.update_task_time(task_type, subject, estimated_time, actual_time)

# Example usage
if __name__ == "__main__":
    scheduler = AcademicAdaptiveScheduler()
    
    # Generate schedule for current week
    today = datetime.now()
    
    # Generate schedule
    schedule = scheduler.generate_schedule(
        ics_file_path='data/calendar.ics',
        date=today,
        health_data='data/health2.json')