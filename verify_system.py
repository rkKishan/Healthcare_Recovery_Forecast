#!/usr/bin/env python3
"""
Verification script for Healthcare Recovery Forecast PDF Report System
Tests all components and provides setup verification
"""

import sys
import subprocess
import os
from pathlib import Path

class VerificationChecker:
    def __init__(self):
        self.checks = []
        self.base_path = Path(__file__).parent
    
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_check(self, name, passed, message=""):
        symbol = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        print(f"  {symbol} {name:<40} [{status}]")
        if message:
            print(f"    → {message}")
        self.checks.append((name, passed))
    
    def check_python_version(self):
        """Check Python version >= 3.8"""
        version = sys.version_info
        passed = version.major >= 3 and version.minor >= 8
        msg = f"Python {version.major}.{version.minor}.{version.micro}"
        self.print_check("Python Version (3.8+)", passed, msg)
    
    def check_required_packages(self):
        """Check if all required packages are installed"""
        required = [
            'fastapi',
            'uvicorn',
            'reportlab',
            'matplotlib',
            'pandas',
            'numpy',
            'seaborn',
            'Pillow'
        ]
        
        print("\n  Checking Python Packages:")
        all_passed = True
        
        for package in required:
            try:
                __import__(package)
                self.print_check(f"  {package}", True)
            except ImportError:
                self.print_check(f"  {package}", False, "Not installed")
                all_passed = False
        
        return all_passed
    
    def check_file_structure(self):
        """Check if all necessary files exist"""
        print("\n  Checking File Structure:")
        
        required_files = {
            'api_server.py': 'FastAPI backend server',
            'ml/pdf_report_generator.py': 'PDF report generator',
            'frontend/components/Reports.tsx': 'Frontend PDF component',
            'requirements.txt': 'Python dependencies',
            'frontend/.env.local.template': 'Environment template'
        }
        
        all_exist = True
        for file_path, description in required_files.items():
            full_path = self.base_path / file_path
            exists = full_path.exists()
            self.print_check(f"  {description}", exists, file_path)
            if not exists:
                all_exist = False
        
        return all_exist
    
    def check_ports(self):
        """Check if required ports are available"""
        print("\n  Checking Ports:")
        
        import socket
        
        ports = {
            8000: 'Backend (FastAPI)',
            9000: 'Frontend (Next.js)'
        }
        
        all_available = True
        for port, service in ports.items():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = s.connect_ex(('localhost', port))
                available = result != 0
                s.close()
                
                status = "Available" if available else "In Use"
                self.print_check(f"  Port {port} ({service})", available, status)
                if not available:
                    all_available = False
            except Exception as e:
                self.print_check(f"  Port {port}", False, str(e))
                all_available = False
        
        return all_available
    
    def check_frontend_config(self):
        """Check frontend environment configuration"""
        print("\n  Checking Frontend Configuration:")
        
        env_path = self.base_path / 'frontend' / '.env.local'
        template_path = self.base_path / 'frontend' / '.env.local.template'
        
        env_exists = env_path.exists()
        template_exists = template_path.exists()
        
        self.print_check("  .env.local exists", env_exists, 
                        "Frontend configured" if env_exists else "Run: npm install and setup .env.local")
        self.print_check("  .env.local.template exists", template_exists, 
                        "Template available for reference")
        
        if env_exists:
            try:
                content = env_path.read_text()
                has_api_url = 'NEXT_PUBLIC_API_BASE_URL' in content
                self.print_check("  API_BASE_URL configured", has_api_url, 
                                "Backend URL is set")
                return has_api_url
            except Exception as e:
                self.print_check("  Read .env.local", False, str(e))
                return False
        
        return False
    
    def test_pdf_generation(self):
        """Test PDF generation without running server"""
        print("\n  Testing PDF Generation Module:")
        
        try:
            sys.path.insert(0, str(self.base_path / 'ml'))
            from pdf_report_generator import PDFReportGenerator
            
            self.print_check("  Import PDFReportGenerator", True, "Module imports successfully")
            
            # Try creating generator
            gen = PDFReportGenerator(hospital_name="Test Hospital")
            self.print_check("  Instantiate Generator", True, "Generator created successfully")
            
            return True
        except Exception as e:
            self.print_check("  PDF Generation", False, str(e))
            return False
    
    def run_all_checks(self):
        """Run all verification checks"""
        self.print_header("Healthcare Recovery Forecast - System Verification")
        
        print("Running system checks...\n")
        
        self.check_python_version()
        pkg_ok = self.check_required_packages()
        file_ok = self.check_file_structure()
        port_ok = self.check_ports()
        env_ok = self.check_frontend_config()
        pdf_ok = self.test_pdf_generation()
        
        # Summary
        print("\n" + "="*60)
        total = len(self.checks)
        passed = sum(1 for _, p in self.checks if p)
        
        print(f"\n  Summary: {passed}/{total} checks passed\n")
        
        if passed == total:
            print("  ✓ All systems ready! You can now run the application.\n")
            print("  Next steps:")
            print("    1. Terminal 1: python api_server.py")
            print("    2. Terminal 2: cd frontend && npm run dev")
            print("    3. Open http://localhost:9000\n")
            return True
        else:
            print("  ✗ Some checks failed. Please review above.\n")
            print("  Fix issues before running the application.\n")
            
            if not pkg_ok:
                print("  → Install packages: pip install -r requirements.txt\n")
            if not file_ok:
                print("  → Check if all files are in correct location\n")
            if not port_ok:
                print("  → Free up ports 8000 and 9000, or modify configuration\n")
            if not env_ok:
                print("  → Copy .env.local.template to .env.local\n")
            
            return False
        
        print("="*60 + "\n")


def main():
    checker = VerificationChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
