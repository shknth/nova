from datetime import datetime, timedelta
import re
from typing import Optional, Dict
import calendar

class TimeParser:
    def __init__(self):
        # Default times for different periods
        self.default_times = {
            'morning': 9,      # 9 AM
            'afternoon': 14,   # 2 PM  
            'evening': 18,     # 6 PM
            'night': 21,       # 9 PM
            'default': 14      # 2 PM if no time specified
        }
        
        # Day name mappings
        self.day_names = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Month name mappings
        self.month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Time period patterns
        self.time_patterns = {
            'relative_days': r'\b(today|tomorrow|yesterday)\b',
            'relative_time': r'\bin\s+(\d+)\s+(hour|hours|minute|minutes|day|days)\b',
            'next_day': r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b',
            'this_day': r'\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b',
            'time_of_day': r'\b(morning|afternoon|evening|night)\b',
            'specific_time': r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?\b',
            'date_format': r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b',
            'numeric_date': r'\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b'
        }
    
    def parse_time(self, time_descriptor: str, reference_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Parse natural language time description to datetime object
        
        Args:
            time_descriptor: Natural language time (e.g., "tomorrow morning", "next Tuesday")
            reference_time: Reference datetime (defaults to now)
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not time_descriptor:
            return None
            
        if reference_time is None:
            reference_time = datetime.now()
            
        # Normalize input
        time_desc = time_descriptor.lower().strip()
        
        try:
            # Try different parsing strategies
            result = (
                self._parse_relative_days(time_desc, reference_time) or
                self._parse_relative_time(time_desc, reference_time) or
                self._parse_next_day(time_desc, reference_time) or
                self._parse_this_day(time_desc, reference_time) or
                self._parse_date_format(time_desc, reference_time) or
                self._parse_numeric_date(time_desc, reference_time) or
                self._parse_default_time(reference_time)
            )
            
            # Apply time of day if specified
            if result:
                result = self._apply_time_of_day(time_desc, result)
                result = self._apply_specific_time(time_desc, result)
            
            return result
            
        except Exception as e:
            print(f"Time parsing error for '{time_descriptor}': {str(e)}")
            return self._parse_default_time(reference_time)
    
    def _parse_relative_days(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse today, tomorrow, yesterday"""
        match = re.search(self.time_patterns['relative_days'], time_desc)
        if not match:
            return None
            
        day_word = match.group(1)
        
        if day_word == 'today':
            target_date = ref_time.date()
        elif day_word == 'tomorrow':
            target_date = (ref_time + timedelta(days=1)).date()
        elif day_word == 'yesterday':
            target_date = (ref_time - timedelta(days=1)).date()
        else:
            return None
            
        # Default to 2 PM
        return datetime.combine(target_date, datetime.min.time().replace(hour=self.default_times['default']))
    
    def _parse_relative_time(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse 'in X hours/days'"""
        match = re.search(self.time_patterns['relative_time'], time_desc)
        if not match:
            return None
            
        amount = int(match.group(1))
        unit = match.group(2).lower()
        
        if unit.startswith('hour'):
            return ref_time + timedelta(hours=amount)
        elif unit.startswith('minute'):
            return ref_time + timedelta(minutes=amount)
        elif unit.startswith('day'):
            return ref_time + timedelta(days=amount)
            
        return None
    
    def _parse_next_day(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse 'next Monday', 'next Tuesday', etc."""
        match = re.search(self.time_patterns['next_day'], time_desc)
        if not match:
            return None
            
        day_name = match.group(1).lower()
        target_weekday = self.day_names.get(day_name)
        
        if target_weekday is None:
            return None
            
        # Find next occurrence of this weekday
        current_weekday = ref_time.weekday()
        days_ahead = target_weekday - current_weekday
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
            
        target_date = ref_time + timedelta(days=days_ahead)
        return datetime.combine(target_date.date(), datetime.min.time().replace(hour=self.default_times['default']))
    
    def _parse_this_day(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse 'this Monday', 'this Tuesday', etc."""
        match = re.search(self.time_patterns['this_day'], time_desc)
        if not match:
            return None
            
        day_name = match.group(1).lower()
        target_weekday = self.day_names.get(day_name)
        
        if target_weekday is None:
            return None
            
        # Find this week's occurrence
        current_weekday = ref_time.weekday()
        days_diff = target_weekday - current_weekday
        
        target_date = ref_time + timedelta(days=days_diff)
        return datetime.combine(target_date.date(), datetime.min.time().replace(hour=self.default_times['default']))
    
    def _parse_date_format(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse 'January 15th', 'March 3rd', etc."""
        match = re.search(self.time_patterns['date_format'], time_desc)
        if not match:
            return None
            
        month_name = match.group(1).lower()
        day = int(match.group(2))
        
        month = self.month_names.get(month_name)
        if month is None:
            return None
            
        # Use current year, or next year if date has passed
        year = ref_time.year
        try:
            target_date = datetime(year, month, day)
            if target_date.date() < ref_time.date():
                target_date = datetime(year + 1, month, day)
        except ValueError:
            return None
            
        return target_date.replace(hour=self.default_times['default'])
    
    def _parse_numeric_date(self, time_desc: str, ref_time: datetime) -> Optional[datetime]:
        """Parse '12/25', '1/15/2024', etc."""
        match = re.search(self.time_patterns['numeric_date'], time_desc)
        if not match:
            return None
            
        month = int(match.group(1))
        day = int(match.group(2))
        year_str = match.group(3)
        
        if year_str:
            year = int(year_str)
            if year < 100:  # Two-digit year
                year += 2000
        else:
            year = ref_time.year
            # If date has passed this year, use next year
            try:
                test_date = datetime(year, month, day)
                if test_date.date() < ref_time.date():
                    year += 1
            except ValueError:
                return None
        
        try:
            target_date = datetime(year, month, day)
            return target_date.replace(hour=self.default_times['default'])
        except ValueError:
            return None
    
    def _parse_default_time(self, ref_time: datetime) -> datetime:
        """Return default time (start of day = 9 AM)"""
        return ref_time.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def _apply_time_of_day(self, time_desc: str, target_datetime: datetime) -> datetime:
        """Apply time of day (morning, afternoon, evening, night)"""
        match = re.search(self.time_patterns['time_of_day'], time_desc)
        if not match:
            return target_datetime
            
        time_period = match.group(1).lower()
        hour = self.default_times.get(time_period, self.default_times['default'])
        
        return target_datetime.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    def _apply_specific_time(self, time_desc: str, target_datetime: datetime) -> datetime:
        """Apply specific time (3 PM, 10:30 AM, etc.)"""
        match = re.search(self.time_patterns['specific_time'], time_desc)
        if not match:
            return target_datetime
            
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        am_pm = match.group(3)
        
        # Handle AM/PM
        if am_pm:
            am_pm = am_pm.lower()
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
        
        # Validate hour
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return target_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
        return target_datetime
    
    def get_time_info(self, time_descriptor: str, reference_time: Optional[datetime] = None) -> Dict:
        """
        Get comprehensive time information
        
        Args:
            time_descriptor: Natural language time description
            reference_time: Reference datetime (defaults to now)
            
        Returns:
            Dictionary with parsed time info and metadata
        """
        if reference_time is None:
            reference_time = datetime.now()
            
        parsed_time = self.parse_time(time_descriptor, reference_time)
        
        if parsed_time:
            time_diff = parsed_time - reference_time
            
            return {
                'original_input': time_descriptor,
                'parsed_datetime': parsed_time.isoformat(),
                'formatted_time': parsed_time.strftime('%Y-%m-%d %H:%M:%S'),
                'human_readable': parsed_time.strftime('%A, %B %d, %Y at %I:%M %p'),
                'is_future': parsed_time > reference_time,
                'hours_from_now': time_diff.total_seconds() / 3600,
                'days_from_now': time_diff.days,
                'reference_time': reference_time.isoformat(),
                'parsing_success': True
            }
        else:
            return {
                'original_input': time_descriptor,
                'parsed_datetime': None,
                'parsing_success': False,
                'error': 'Could not parse time description'
            }

def main():
    """Test the TimeParser with various inputs"""
    parser = TimeParser()
    
    test_cases = [
        "tomorrow",
        "tomorrow morning", 
        "next Tuesday",
        "this evening",
        "in 3 hours",
        "January 15th",
        "March 3rd at 2 PM",
        "12/25",
        "today at 10:30 AM",
        "next Friday evening",
        "in 2 days",
        "February 14th at 7 PM"
    ]
    
    print("🕐 TIME PARSER TESTING")
    print("=" * 50)
    
    for test_case in test_cases:
        result = parser.get_time_info(test_case)
        
        if result['parsing_success']:
            print(f"Input: '{test_case}'")
            print(f"  → {result['human_readable']}")
            print(f"  → {result['formatted_time']}")
            print(f"  → {result['hours_from_now']:.1f} hours from now")
            print()
        else:
            print(f"❌ Failed to parse: '{test_case}'")
            print()

if __name__ == "__main__":
    main()

