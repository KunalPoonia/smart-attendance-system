#!/usr/bin/env python3
"""
Advanced Attendance Analytics Module for Smart Attendance System
Provides comprehensive analytics, reporting, and statistical analysis
for attendance data with support for trends, predictions, and insights.

Author: ayushap18
Date: January 2026
ECWoC 2026 Contribution
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Union
import statistics
import csv
import io

# Configure logging
logger = logging.getLogger(__name__)


class AttendanceStatistics:
    """
    Comprehensive attendance statistics calculator.
    Provides various statistical measures for attendance analysis.
    """
    
    def __init__(self, records: List[Dict] = None):
        """
        Initialize statistics calculator with attendance records.
        
        Args:
            records: List of attendance record dictionaries
        """
        self.records = records or []
        self._cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def _invalidate_cache(self):
        """Invalidate the statistics cache."""
        self._cache = {}
        self._cache_timestamp = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_ttl
    
    def set_records(self, records: List[Dict]):
        """
        Update the records and invalidate cache.
        
        Args:
            records: New list of attendance records
        """
        self.records = records
        self._invalidate_cache()
    
    def calculate_attendance_rate(self, student_id: str = None) -> float:
        """
        Calculate overall attendance rate or for specific student.
        
        Args:
            student_id: Optional student ID to filter by
            
        Returns:
            Attendance rate as percentage (0-100)
        """
        try:
            filtered_records = self.records
            if student_id:
                filtered_records = [r for r in self.records if r.get('student_id') == student_id]
            
            if not filtered_records:
                return 0.0
            
            present_count = len([r for r in filtered_records if r.get('status') in ['Present', 'Late']])
            total_count = len(filtered_records)
            
            return round((present_count / total_count) * 100, 2) if total_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating attendance rate: {e}")
            return 0.0
    
    def calculate_punctuality_rate(self, student_id: str = None) -> float:
        """
        Calculate punctuality rate (on-time attendance).
        
        Args:
            student_id: Optional student ID to filter by
            
        Returns:
            Punctuality rate as percentage (0-100)
        """
        try:
            filtered_records = self.records
            if student_id:
                filtered_records = [r for r in self.records if r.get('student_id') == student_id]
            
            if not filtered_records:
                return 0.0
            
            on_time_count = len([r for r in filtered_records if r.get('status') == 'Present'])
            attended_count = len([r for r in filtered_records if r.get('status') in ['Present', 'Late']])
            
            return round((on_time_count / attended_count) * 100, 2) if attended_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating punctuality rate: {e}")
            return 0.0
    
    def get_status_distribution(self) -> Dict[str, int]:
        """
        Get distribution of attendance statuses.
        
        Returns:
            Dictionary with status counts
        """
        distribution = defaultdict(int)
        for record in self.records:
            status = record.get('status', 'Unknown')
            distribution[status] += 1
        return dict(distribution)
    
    def get_daily_statistics(self, target_date: date = None) -> Dict[str, Any]:
        """
        Get attendance statistics for a specific day.
        
        Args:
            target_date: Date to analyze (defaults to today)
            
        Returns:
            Dictionary with daily statistics
        """
        target_date = target_date or date.today()
        
        daily_records = [
            r for r in self.records 
            if self._parse_date(r.get('date')) == target_date
        ]
        
        return {
            'date': target_date.isoformat(),
            'total_records': len(daily_records),
            'present': len([r for r in daily_records if r.get('status') == 'Present']),
            'late': len([r for r in daily_records if r.get('status') == 'Late']),
            'absent': len([r for r in daily_records if r.get('status') == 'Absent']),
            'attendance_rate': self._calculate_rate(daily_records, ['Present', 'Late']),
            'punctuality_rate': self._calculate_rate(
                [r for r in daily_records if r.get('status') in ['Present', 'Late']], 
                ['Present']
            )
        }
    
    def get_weekly_statistics(self, start_date: date = None) -> Dict[str, Any]:
        """
        Get attendance statistics for a week.
        
        Args:
            start_date: Start of the week (defaults to current week's Monday)
            
        Returns:
            Dictionary with weekly statistics
        """
        if start_date is None:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        
        end_date = start_date + timedelta(days=6)
        
        weekly_records = [
            r for r in self.records
            if start_date <= self._parse_date(r.get('date')) <= end_date
        ]
        
        daily_breakdown = {}
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_name = current_date.strftime('%A')
            daily_breakdown[day_name] = self.get_daily_statistics(current_date)
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_records': len(weekly_records),
            'average_attendance_rate': self._calculate_rate(weekly_records, ['Present', 'Late']),
            'average_punctuality_rate': self._calculate_rate(
                [r for r in weekly_records if r.get('status') in ['Present', 'Late']],
                ['Present']
            ),
            'daily_breakdown': daily_breakdown
        }
    
    def get_monthly_statistics(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        Get attendance statistics for a month.
        
        Args:
            year: Year (defaults to current year)
            month: Month (defaults to current month)
            
        Returns:
            Dictionary with monthly statistics
        """
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        monthly_records = [
            r for r in self.records
            if self._is_in_month(r.get('date'), year, month)
        ]
        
        # Calculate weekly breakdown
        weeks = defaultdict(list)
        for record in monthly_records:
            record_date = self._parse_date(record.get('date'))
            if record_date:
                week_num = record_date.isocalendar()[1]
                weeks[f"Week {week_num}"].append(record)
        
        weekly_breakdown = {}
        for week, records in weeks.items():
            weekly_breakdown[week] = {
                'total': len(records),
                'present': len([r for r in records if r.get('status') == 'Present']),
                'late': len([r for r in records if r.get('status') == 'Late']),
                'absent': len([r for r in records if r.get('status') == 'Absent']),
                'attendance_rate': self._calculate_rate(records, ['Present', 'Late'])
            }
        
        return {
            'year': year,
            'month': month,
            'month_name': date(year, month, 1).strftime('%B'),
            'total_records': len(monthly_records),
            'present_count': len([r for r in monthly_records if r.get('status') == 'Present']),
            'late_count': len([r for r in monthly_records if r.get('status') == 'Late']),
            'absent_count': len([r for r in monthly_records if r.get('status') == 'Absent']),
            'attendance_rate': self._calculate_rate(monthly_records, ['Present', 'Late']),
            'punctuality_rate': self._calculate_rate(
                [r for r in monthly_records if r.get('status') in ['Present', 'Late']],
                ['Present']
            ),
            'weekly_breakdown': weekly_breakdown
        }
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value).date()
            except ValueError:
                try:
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    return None
        return None
    
    def _is_in_month(self, date_value: Any, year: int, month: int) -> bool:
        """Check if date is in specified month."""
        parsed_date = self._parse_date(date_value)
        if not parsed_date:
            return False
        return parsed_date.year == year and parsed_date.month == month
    
    def _calculate_rate(self, records: List[Dict], target_statuses: List[str]) -> float:
        """Calculate rate of records with target statuses."""
        if not records:
            return 0.0
        matching = len([r for r in records if r.get('status') in target_statuses])
        return round((matching / len(records)) * 100, 2)


class AttendanceTrendAnalyzer:
    """
    Analyzer for attendance trends and patterns.
    Identifies trends, anomalies, and predictions.
    """
    
    def __init__(self, records: List[Dict] = None):
        """
        Initialize trend analyzer.
        
        Args:
            records: List of attendance records
        """
        self.records = records or []
        self.statistics = AttendanceStatistics(records)
    
    def set_records(self, records: List[Dict]):
        """Update records for analysis."""
        self.records = records
        self.statistics.set_records(records)
    
    def analyze_attendance_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze attendance trend over specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend analysis results
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        daily_rates = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_stats = self.statistics.get_daily_statistics(current_date)
            if daily_stats['total_records'] > 0:
                daily_rates.append({
                    'date': current_date.isoformat(),
                    'rate': daily_stats['attendance_rate']
                })
            current_date += timedelta(days=1)
        
        if len(daily_rates) < 2:
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'change_rate': 0,
                'data_points': daily_rates
            }
        
        # Calculate trend direction
        rates = [d['rate'] for d in daily_rates]
        first_half_avg = statistics.mean(rates[:len(rates)//2]) if rates[:len(rates)//2] else 0
        second_half_avg = statistics.mean(rates[len(rates)//2:]) if rates[len(rates)//2:] else 0
        
        change_rate = second_half_avg - first_half_avg
        
        if change_rate > 2:
            direction = 'improving'
            trend = 'positive'
        elif change_rate < -2:
            direction = 'declining'
            trend = 'negative'
        else:
            direction = 'stable'
            trend = 'neutral'
        
        return {
            'trend': trend,
            'direction': direction,
            'change_rate': round(change_rate, 2),
            'average_rate': round(statistics.mean(rates), 2) if rates else 0,
            'min_rate': round(min(rates), 2) if rates else 0,
            'max_rate': round(max(rates), 2) if rates else 0,
            'std_deviation': round(statistics.stdev(rates), 2) if len(rates) > 1 else 0,
            'data_points': daily_rates,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }
    
    def identify_patterns(self) -> Dict[str, Any]:
        """
        Identify attendance patterns in the data.
        
        Returns:
            Pattern analysis results
        """
        patterns = {
            'day_of_week': self._analyze_day_pattern(),
            'time_of_day': self._analyze_time_pattern(),
            'department': self._analyze_department_pattern(),
            'seasonal': self._analyze_seasonal_pattern()
        }
        
        return patterns
    
    def _analyze_day_pattern(self) -> Dict[str, Any]:
        """Analyze attendance patterns by day of week."""
        day_data = defaultdict(list)
        
        for record in self.records:
            record_date = self.statistics._parse_date(record.get('date'))
            if record_date:
                day_name = record_date.strftime('%A')
                is_present = record.get('status') in ['Present', 'Late']
                day_data[day_name].append(1 if is_present else 0)
        
        day_rates = {}
        for day, values in day_data.items():
            if values:
                day_rates[day] = round(statistics.mean(values) * 100, 2)
        
        best_day = max(day_rates, key=day_rates.get) if day_rates else None
        worst_day = min(day_rates, key=day_rates.get) if day_rates else None
        
        return {
            'rates_by_day': day_rates,
            'best_day': best_day,
            'worst_day': worst_day,
            'variation': round(max(day_rates.values()) - min(day_rates.values()), 2) if day_rates else 0
        }
    
    def _analyze_time_pattern(self) -> Dict[str, Any]:
        """Analyze attendance patterns by time of day."""
        time_slots = {
            'early_morning': (6, 9),    # 6 AM - 9 AM
            'morning': (9, 12),          # 9 AM - 12 PM
            'afternoon': (12, 15),       # 12 PM - 3 PM
            'late_afternoon': (15, 18),  # 3 PM - 6 PM
            'evening': (18, 21)          # 6 PM - 9 PM
        }
        
        slot_data = defaultdict(list)
        
        for record in self.records:
            time_in = record.get('time_in')
            if time_in:
                hour = self._parse_hour(time_in)
                if hour is not None:
                    for slot_name, (start, end) in time_slots.items():
                        if start <= hour < end:
                            is_present = record.get('status') in ['Present', 'Late']
                            slot_data[slot_name].append(1 if is_present else 0)
                            break
        
        slot_rates = {}
        for slot, values in slot_data.items():
            if values:
                slot_rates[slot] = round(statistics.mean(values) * 100, 2)
        
        return {
            'rates_by_slot': slot_rates,
            'peak_slot': max(slot_rates, key=slot_rates.get) if slot_rates else None,
            'low_slot': min(slot_rates, key=slot_rates.get) if slot_rates else None
        }
    
    def _analyze_department_pattern(self) -> Dict[str, Any]:
        """Analyze attendance patterns by department."""
        dept_data = defaultdict(list)
        
        for record in self.records:
            dept = record.get('department', 'Unknown')
            is_present = record.get('status') in ['Present', 'Late']
            dept_data[dept].append(1 if is_present else 0)
        
        dept_rates = {}
        for dept, values in dept_data.items():
            if values:
                dept_rates[dept] = {
                    'rate': round(statistics.mean(values) * 100, 2),
                    'total_records': len(values)
                }
        
        return {
            'rates_by_department': dept_rates,
            'best_department': max(dept_rates, key=lambda x: dept_rates[x]['rate']) if dept_rates else None,
            'needs_attention': [
                dept for dept, data in dept_rates.items() 
                if data['rate'] < 75
            ]
        }
    
    def _analyze_seasonal_pattern(self) -> Dict[str, Any]:
        """Analyze attendance patterns by month/season."""
        month_data = defaultdict(list)
        
        for record in self.records:
            record_date = self.statistics._parse_date(record.get('date'))
            if record_date:
                month_name = record_date.strftime('%B')
                is_present = record.get('status') in ['Present', 'Late']
                month_data[month_name].append(1 if is_present else 0)
        
        month_rates = {}
        for month, values in month_data.items():
            if values:
                month_rates[month] = round(statistics.mean(values) * 100, 2)
        
        return {
            'rates_by_month': month_rates,
            'best_month': max(month_rates, key=month_rates.get) if month_rates else None,
            'worst_month': min(month_rates, key=month_rates.get) if month_rates else None
        }
    
    def _parse_hour(self, time_value: Any) -> Optional[int]:
        """Parse hour from time value."""
        if isinstance(time_value, datetime):
            return time_value.hour
        if isinstance(time_value, str):
            try:
                return datetime.strptime(time_value, '%H:%M:%S').hour
            except ValueError:
                try:
                    return datetime.strptime(time_value, '%H:%M').hour
                except ValueError:
                    return None
        return None
    
    def predict_attendance(self, target_date: date = None) -> Dict[str, Any]:
        """
        Predict attendance for a future date based on historical patterns.
        
        Args:
            target_date: Date to predict for (defaults to tomorrow)
            
        Returns:
            Prediction results
        """
        target_date = target_date or (date.today() + timedelta(days=1))
        day_name = target_date.strftime('%A')
        
        # Get historical data for same day of week
        historical_rates = []
        for record in self.records:
            record_date = self.statistics._parse_date(record.get('date'))
            if record_date and record_date.strftime('%A') == day_name:
                is_present = record.get('status') in ['Present', 'Late']
                historical_rates.append(1 if is_present else 0)
        
        if not historical_rates:
            return {
                'target_date': target_date.isoformat(),
                'predicted_rate': None,
                'confidence': 'low',
                'message': 'Insufficient historical data for prediction'
            }
        
        predicted_rate = statistics.mean(historical_rates) * 100
        std_dev = statistics.stdev(historical_rates) * 100 if len(historical_rates) > 1 else 0
        
        # Determine confidence based on data quantity and variance
        if len(historical_rates) >= 10 and std_dev < 15:
            confidence = 'high'
        elif len(historical_rates) >= 5 and std_dev < 25:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'target_date': target_date.isoformat(),
            'day_of_week': day_name,
            'predicted_rate': round(predicted_rate, 2),
            'confidence': confidence,
            'confidence_interval': {
                'lower': round(max(0, predicted_rate - std_dev), 2),
                'upper': round(min(100, predicted_rate + std_dev), 2)
            },
            'historical_data_points': len(historical_rates)
        }


class AttendanceReportGenerator:
    """
    Generator for attendance reports in various formats.
    """
    
    def __init__(self, records: List[Dict] = None):
        """
        Initialize report generator.
        
        Args:
            records: List of attendance records
        """
        self.records = records or []
        self.statistics = AttendanceStatistics(records)
        self.trend_analyzer = AttendanceTrendAnalyzer(records)
    
    def set_records(self, records: List[Dict]):
        """Update records for report generation."""
        self.records = records
        self.statistics.set_records(records)
        self.trend_analyzer.set_records(records)
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Returns:
            Summary report dictionary
        """
        trend_analysis = self.trend_analyzer.analyze_attendance_trend(30)
        patterns = self.trend_analyzer.identify_patterns()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'summary',
            'overview': {
                'total_records': len(self.records),
                'overall_attendance_rate': self.statistics.calculate_attendance_rate(),
                'overall_punctuality_rate': self.statistics.calculate_punctuality_rate(),
                'status_distribution': self.statistics.get_status_distribution()
            },
            'trend_analysis': trend_analysis,
            'patterns': patterns,
            'weekly_summary': self.statistics.get_weekly_statistics(),
            'monthly_summary': self.statistics.get_monthly_statistics()
        }
    
    def generate_student_report(self, student_id: str) -> Dict[str, Any]:
        """
        Generate report for specific student.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Student report dictionary
        """
        student_records = [r for r in self.records if r.get('student_id') == student_id]
        
        if not student_records:
            return {
                'student_id': student_id,
                'error': 'No records found for student'
            }
        
        student_stats = AttendanceStatistics(student_records)
        
        # Get student info from first record
        student_info = {
            'student_id': student_id,
            'name': student_records[0].get('name', 'Unknown'),
            'department': student_records[0].get('department', 'Unknown'),
            'year': student_records[0].get('year', 'Unknown'),
            'section': student_records[0].get('section', 'Unknown')
        }
        
        return {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'student',
            'student_info': student_info,
            'statistics': {
                'total_sessions': len(student_records),
                'attendance_rate': student_stats.calculate_attendance_rate(),
                'punctuality_rate': student_stats.calculate_punctuality_rate(),
                'status_distribution': student_stats.get_status_distribution()
            },
            'monthly_summary': student_stats.get_monthly_statistics(),
            'attendance_history': [
                {
                    'date': r.get('date'),
                    'status': r.get('status'),
                    'time_in': r.get('time_in')
                }
                for r in sorted(student_records, key=lambda x: x.get('date', ''), reverse=True)[:30]
            ]
        }
    
    def generate_department_report(self, department: str) -> Dict[str, Any]:
        """
        Generate report for specific department.
        
        Args:
            department: Department name
            
        Returns:
            Department report dictionary
        """
        dept_records = [r for r in self.records if r.get('department') == department]
        
        if not dept_records:
            return {
                'department': department,
                'error': 'No records found for department'
            }
        
        dept_stats = AttendanceStatistics(dept_records)
        dept_analyzer = AttendanceTrendAnalyzer(dept_records)
        
        # Get unique students in department
        unique_students = set(r.get('student_id') for r in dept_records if r.get('student_id'))
        
        # Calculate per-student statistics
        student_performance = []
        for student_id in unique_students:
            student_records = [r for r in dept_records if r.get('student_id') == student_id]
            if student_records:
                student_stats = AttendanceStatistics(student_records)
                student_performance.append({
                    'student_id': student_id,
                    'name': student_records[0].get('name', 'Unknown'),
                    'attendance_rate': student_stats.calculate_attendance_rate(),
                    'total_sessions': len(student_records)
                })
        
        # Sort by attendance rate
        student_performance.sort(key=lambda x: x['attendance_rate'], reverse=True)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'department',
            'department': department,
            'overview': {
                'total_students': len(unique_students),
                'total_records': len(dept_records),
                'average_attendance_rate': dept_stats.calculate_attendance_rate(),
                'average_punctuality_rate': dept_stats.calculate_punctuality_rate()
            },
            'trend_analysis': dept_analyzer.analyze_attendance_trend(30),
            'top_performers': student_performance[:5],
            'needs_attention': [s for s in student_performance if s['attendance_rate'] < 75],
            'monthly_summary': dept_stats.get_monthly_statistics()
        }
    
    def export_to_csv(self, report_type: str = 'summary', **kwargs) -> str:
        """
        Export report data to CSV format.
        
        Args:
            report_type: Type of report ('summary', 'student', 'department')
            **kwargs: Additional arguments for specific report types
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == 'summary':
            writer.writerow(['Attendance Summary Report'])
            writer.writerow(['Generated At', datetime.now().isoformat()])
            writer.writerow([])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Records', len(self.records)])
            writer.writerow(['Overall Attendance Rate', f"{self.statistics.calculate_attendance_rate()}%"])
            writer.writerow(['Overall Punctuality Rate', f"{self.statistics.calculate_punctuality_rate()}%"])
            writer.writerow([])
            writer.writerow(['Status Distribution'])
            for status, count in self.statistics.get_status_distribution().items():
                writer.writerow([status, count])
                
        elif report_type == 'records':
            writer.writerow(['Date', 'Student ID', 'Name', 'Department', 'Status', 'Time In'])
            for record in self.records:
                writer.writerow([
                    record.get('date', ''),
                    record.get('student_id', ''),
                    record.get('name', ''),
                    record.get('department', ''),
                    record.get('status', ''),
                    record.get('time_in', '')
                ])
        
        return output.getvalue()
    
    def export_to_json(self, report_type: str = 'summary', **kwargs) -> str:
        """
        Export report data to JSON format.
        
        Args:
            report_type: Type of report
            **kwargs: Additional arguments for specific report types
            
        Returns:
            JSON string
        """
        if report_type == 'summary':
            report = self.generate_summary_report()
        elif report_type == 'student':
            student_id = kwargs.get('student_id')
            report = self.generate_student_report(student_id) if student_id else {'error': 'student_id required'}
        elif report_type == 'department':
            department = kwargs.get('department')
            report = self.generate_department_report(department) if department else {'error': 'department required'}
        else:
            report = {'error': 'Invalid report type'}
        
        return json.dumps(report, indent=2, default=str)


class AttendanceAlertSystem:
    """
    Alert system for attendance monitoring.
    Generates alerts for various attendance conditions.
    """
    
    ALERT_LEVELS = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1,
        'info': 0
    }
    
    def __init__(self, records: List[Dict] = None, thresholds: Dict[str, float] = None):
        """
        Initialize alert system.
        
        Args:
            records: List of attendance records
            thresholds: Custom alert thresholds
        """
        self.records = records or []
        self.statistics = AttendanceStatistics(records)
        
        # Default thresholds
        self.thresholds = thresholds or {
            'critical_attendance': 50.0,    # Below 50% is critical
            'low_attendance': 75.0,          # Below 75% needs attention
            'chronic_absence': 3,             # 3+ consecutive absences
            'late_pattern': 5,                # 5+ late arrivals in period
            'perfect_attendance_days': 30     # Days for perfect attendance recognition
        }
        
        self.alerts = []
    
    def set_records(self, records: List[Dict]):
        """Update records and regenerate alerts."""
        self.records = records
        self.statistics.set_records(records)
        self.alerts = []
    
    def generate_alerts(self) -> List[Dict[str, Any]]:
        """
        Generate all applicable alerts based on current data.
        
        Returns:
            List of alert dictionaries
        """
        self.alerts = []
        
        # Check overall attendance
        self._check_overall_attendance()
        
        # Check individual student attendance
        self._check_student_attendance()
        
        # Check department attendance
        self._check_department_attendance()
        
        # Check for chronic absences
        self._check_chronic_absences()
        
        # Check for late patterns
        self._check_late_patterns()
        
        # Check for perfect attendance
        self._check_perfect_attendance()
        
        # Sort alerts by level
        self.alerts.sort(key=lambda x: self.ALERT_LEVELS.get(x['level'], 0), reverse=True)
        
        return self.alerts
    
    def _add_alert(self, level: str, category: str, message: str, details: Dict = None):
        """Add an alert to the list."""
        self.alerts.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {}
        })
    
    def _check_overall_attendance(self):
        """Check overall attendance rates."""
        rate = self.statistics.calculate_attendance_rate()
        
        if rate < self.thresholds['critical_attendance']:
            self._add_alert(
                'critical',
                'overall_attendance',
                f'Critical: Overall attendance rate is {rate}%',
                {'rate': rate, 'threshold': self.thresholds['critical_attendance']}
            )
        elif rate < self.thresholds['low_attendance']:
            self._add_alert(
                'high',
                'overall_attendance',
                f'Warning: Overall attendance rate is {rate}%',
                {'rate': rate, 'threshold': self.thresholds['low_attendance']}
            )
    
    def _check_student_attendance(self):
        """Check individual student attendance."""
        student_ids = set(r.get('student_id') for r in self.records if r.get('student_id'))
        
        for student_id in student_ids:
            student_records = [r for r in self.records if r.get('student_id') == student_id]
            if len(student_records) < 5:  # Skip if insufficient data
                continue
            
            student_stats = AttendanceStatistics(student_records)
            rate = student_stats.calculate_attendance_rate()
            
            if rate < self.thresholds['critical_attendance']:
                self._add_alert(
                    'critical',
                    'student_attendance',
                    f'Critical attendance for student {student_id}: {rate}%',
                    {
                        'student_id': student_id,
                        'name': student_records[0].get('name', 'Unknown'),
                        'rate': rate
                    }
                )
            elif rate < self.thresholds['low_attendance']:
                self._add_alert(
                    'medium',
                    'student_attendance',
                    f'Low attendance for student {student_id}: {rate}%',
                    {
                        'student_id': student_id,
                        'name': student_records[0].get('name', 'Unknown'),
                        'rate': rate
                    }
                )
    
    def _check_department_attendance(self):
        """Check department-level attendance."""
        departments = set(r.get('department') for r in self.records if r.get('department'))
        
        for dept in departments:
            dept_records = [r for r in self.records if r.get('department') == dept]
            if len(dept_records) < 10:  # Skip if insufficient data
                continue
            
            dept_stats = AttendanceStatistics(dept_records)
            rate = dept_stats.calculate_attendance_rate()
            
            if rate < self.thresholds['critical_attendance']:
                self._add_alert(
                    'high',
                    'department_attendance',
                    f'Critical attendance in {dept} department: {rate}%',
                    {'department': dept, 'rate': rate}
                )
            elif rate < self.thresholds['low_attendance']:
                self._add_alert(
                    'medium',
                    'department_attendance',
                    f'Low attendance in {dept} department: {rate}%',
                    {'department': dept, 'rate': rate}
                )
    
    def _check_chronic_absences(self):
        """Check for chronic absence patterns."""
        student_ids = set(r.get('student_id') for r in self.records if r.get('student_id'))
        
        for student_id in student_ids:
            student_records = sorted(
                [r for r in self.records if r.get('student_id') == student_id],
                key=lambda x: x.get('date', '')
            )
            
            # Count consecutive absences at the end
            consecutive_absences = 0
            for record in reversed(student_records):
                if record.get('status') == 'Absent':
                    consecutive_absences += 1
                else:
                    break
            
            if consecutive_absences >= self.thresholds['chronic_absence']:
                self._add_alert(
                    'high',
                    'chronic_absence',
                    f'Student {student_id} has {consecutive_absences} consecutive absences',
                    {
                        'student_id': student_id,
                        'name': student_records[0].get('name', 'Unknown') if student_records else 'Unknown',
                        'consecutive_absences': consecutive_absences
                    }
                )
    
    def _check_late_patterns(self):
        """Check for chronic late arrival patterns."""
        # Look at last 30 days
        cutoff_date = date.today() - timedelta(days=30)
        
        student_ids = set(r.get('student_id') for r in self.records if r.get('student_id'))
        
        for student_id in student_ids:
            recent_records = [
                r for r in self.records 
                if r.get('student_id') == student_id and
                self.statistics._parse_date(r.get('date')) and
                self.statistics._parse_date(r.get('date')) >= cutoff_date
            ]
            
            late_count = len([r for r in recent_records if r.get('status') == 'Late'])
            
            if late_count >= self.thresholds['late_pattern']:
                self._add_alert(
                    'medium',
                    'late_pattern',
                    f'Student {student_id} has been late {late_count} times in last 30 days',
                    {
                        'student_id': student_id,
                        'name': recent_records[0].get('name', 'Unknown') if recent_records else 'Unknown',
                        'late_count': late_count
                    }
                )
    
    def _check_perfect_attendance(self):
        """Check for perfect attendance achievements."""
        cutoff_date = date.today() - timedelta(days=self.thresholds['perfect_attendance_days'])
        
        student_ids = set(r.get('student_id') for r in self.records if r.get('student_id'))
        
        for student_id in student_ids:
            recent_records = [
                r for r in self.records 
                if r.get('student_id') == student_id and
                self.statistics._parse_date(r.get('date')) and
                self.statistics._parse_date(r.get('date')) >= cutoff_date
            ]
            
            if len(recent_records) < 15:  # Need minimum records
                continue
            
            all_present = all(r.get('status') == 'Present' for r in recent_records)
            
            if all_present:
                self._add_alert(
                    'info',
                    'perfect_attendance',
                    f'Congratulations! Student {student_id} has perfect attendance',
                    {
                        'student_id': student_id,
                        'name': recent_records[0].get('name', 'Unknown') if recent_records else 'Unknown',
                        'days': len(recent_records)
                    }
                )
    
    def get_alerts_by_level(self, level: str) -> List[Dict]:
        """Get alerts filtered by level."""
        return [a for a in self.alerts if a['level'] == level]
    
    def get_alerts_by_category(self, category: str) -> List[Dict]:
        """Get alerts filtered by category."""
        return [a for a in self.alerts if a['category'] == category]


class AttendanceDataValidator:
    """
    Validator for attendance data integrity.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.errors = []
        self.warnings = []
    
    def validate_record(self, record: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a single attendance record.
        
        Args:
            record: Attendance record dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required fields
        required_fields = ['student_id', 'date', 'status']
        for field in required_fields:
            if not record.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate status
        valid_statuses = ['Present', 'Absent', 'Late', 'Excused']
        if record.get('status') and record['status'] not in valid_statuses:
            errors.append(f"Invalid status: {record['status']}. Must be one of {valid_statuses}")
        
        # Validate date format
        date_value = record.get('date')
        if date_value:
            try:
                if isinstance(date_value, str):
                    datetime.fromisoformat(date_value)
            except ValueError:
                errors.append(f"Invalid date format: {date_value}")
        
        # Validate time format
        time_value = record.get('time_in')
        if time_value and isinstance(time_value, str):
            try:
                datetime.strptime(time_value, '%H:%M:%S')
            except ValueError:
                try:
                    datetime.strptime(time_value, '%H:%M')
                except ValueError:
                    errors.append(f"Invalid time format: {time_value}")
        
        return len(errors) == 0, errors
    
    def validate_records(self, records: List[Dict]) -> Dict[str, Any]:
        """
        Validate multiple attendance records.
        
        Args:
            records: List of attendance records
            
        Returns:
            Validation results dictionary
        """
        self.errors = []
        self.warnings = []
        
        valid_count = 0
        invalid_count = 0
        invalid_records = []
        
        for i, record in enumerate(records):
            is_valid, errors = self.validate_record(record)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_records.append({
                    'index': i,
                    'record': record,
                    'errors': errors
                })
                self.errors.extend(errors)
        
        # Check for duplicates
        seen = set()
        duplicates = []
        for record in records:
            key = (record.get('student_id'), record.get('date'))
            if key in seen:
                duplicates.append(key)
                self.warnings.append(f"Duplicate record for student {key[0]} on {key[1]}")
            seen.add(key)
        
        return {
            'total_records': len(records),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'duplicate_count': len(duplicates),
            'is_valid': invalid_count == 0,
            'invalid_records': invalid_records,
            'duplicates': duplicates,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def sanitize_record(self, record: Dict) -> Dict:
        """
        Sanitize and normalize a record.
        
        Args:
            record: Raw attendance record
            
        Returns:
            Sanitized record
        """
        sanitized = {}
        
        # Sanitize string fields
        string_fields = ['student_id', 'name', 'department', 'section', 'status']
        for field in string_fields:
            value = record.get(field)
            if value:
                sanitized[field] = str(value).strip()
        
        # Normalize status
        status = sanitized.get('status', '').capitalize()
        if status in ['Present', 'Absent', 'Late', 'Excused']:
            sanitized['status'] = status
        
        # Parse and normalize date
        date_value = record.get('date')
        if date_value:
            if isinstance(date_value, date):
                sanitized['date'] = date_value.isoformat()
            elif isinstance(date_value, datetime):
                sanitized['date'] = date_value.date().isoformat()
            elif isinstance(date_value, str):
                try:
                    sanitized['date'] = datetime.fromisoformat(date_value).date().isoformat()
                except ValueError:
                    sanitized['date'] = date_value
        
        # Parse and normalize time
        time_value = record.get('time_in')
        if time_value:
            if isinstance(time_value, datetime):
                sanitized['time_in'] = time_value.strftime('%H:%M:%S')
            elif isinstance(time_value, str):
                sanitized['time_in'] = time_value
        
        # Copy other fields
        for key, value in record.items():
            if key not in sanitized:
                sanitized[key] = value
        
        return sanitized


# Convenience functions for quick access

def calculate_attendance_stats(records: List[Dict]) -> Dict[str, Any]:
    """
    Quick function to calculate attendance statistics.
    
    Args:
        records: List of attendance records
        
    Returns:
        Statistics dictionary
    """
    stats = AttendanceStatistics(records)
    return {
        'attendance_rate': stats.calculate_attendance_rate(),
        'punctuality_rate': stats.calculate_punctuality_rate(),
        'status_distribution': stats.get_status_distribution(),
        'daily_stats': stats.get_daily_statistics(),
        'weekly_stats': stats.get_weekly_statistics(),
        'monthly_stats': stats.get_monthly_statistics()
    }


def analyze_attendance_trends(records: List[Dict], days: int = 30) -> Dict[str, Any]:
    """
    Quick function to analyze attendance trends.
    
    Args:
        records: List of attendance records
        days: Number of days to analyze
        
    Returns:
        Trend analysis results
    """
    analyzer = AttendanceTrendAnalyzer(records)
    return {
        'trend': analyzer.analyze_attendance_trend(days),
        'patterns': analyzer.identify_patterns(),
        'prediction': analyzer.predict_attendance()
    }


def generate_attendance_alerts(records: List[Dict], thresholds: Dict = None) -> List[Dict]:
    """
    Quick function to generate attendance alerts.
    
    Args:
        records: List of attendance records
        thresholds: Custom alert thresholds
        
    Returns:
        List of alerts
    """
    alert_system = AttendanceAlertSystem(records, thresholds)
    return alert_system.generate_alerts()


def validate_attendance_data(records: List[Dict]) -> Dict[str, Any]:
    """
    Quick function to validate attendance data.
    
    Args:
        records: List of attendance records
        
    Returns:
        Validation results
    """
    validator = AttendanceDataValidator()
    return validator.validate_records(records)


if __name__ == '__main__':
    # Example usage
    sample_records = [
        {'student_id': 'STU001', 'name': 'John Doe', 'date': '2026-01-06', 'status': 'Present', 'time_in': '09:00:00', 'department': 'CS'},
        {'student_id': 'STU002', 'name': 'Jane Smith', 'date': '2026-01-06', 'status': 'Late', 'time_in': '09:15:00', 'department': 'CS'},
        {'student_id': 'STU003', 'name': 'Bob Johnson', 'date': '2026-01-06', 'status': 'Absent', 'department': 'IT'},
    ]
    
    print("=== Attendance Analytics Demo ===\n")
    
    # Calculate statistics
    stats = calculate_attendance_stats(sample_records)
    print(f"Attendance Rate: {stats['attendance_rate']}%")
    print(f"Punctuality Rate: {stats['punctuality_rate']}%")
    print(f"Status Distribution: {stats['status_distribution']}")
    
    # Generate alerts
    alerts = generate_attendance_alerts(sample_records)
    print(f"\nAlerts Generated: {len(alerts)}")
    for alert in alerts:
        print(f"  [{alert['level'].upper()}] {alert['message']}")
    
    # Validate data
    validation = validate_attendance_data(sample_records)
    print(f"\nData Validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
    print(f"  Valid Records: {validation['valid_count']}/{validation['total_records']}")
