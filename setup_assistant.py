#!/usr/bin/env python
"""
Virtual Shopping Assistant - Initial Setup Script

This script helps set up the Virtual Shopping Assistant for the first time.
It performs all necessary checks and setup steps.

Usage:
    python setup_assistant.py
"""

import os
import sys
import subprocess


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(step_num, text):
    """Print a step number and description"""
    print(f"[Step {step_num}] {text}")


def check_env_file():
    """Check if .env file exists and has OPENAI_API_KEY"""
    print_step(1, "Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\nPlease create a .env file with:")
        print("OPENAI_API_KEY=sk-your-api-key-here")
        print("OPENAI_MODEL=gpt-4o-mini")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        
    if 'OPENAI_API_KEY' not in content:
        print("❌ OPENAI_API_KEY not found in .env file!")
        print("\nPlease add to your .env file:")
        print("OPENAI_API_KEY=sk-your-api-key-here")
        print("OPENAI_MODEL=gpt-4o-mini")
        return False
    
    if 'OPENAI_API_KEY=' in content and 'sk-' not in content:
        print("⚠️  Warning: OPENAI_API_KEY appears to be empty or invalid")
        print("Please set a valid OpenAI API key in .env file")
        return False
    
    print("✅ Environment file configured")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    print_step(2, "Checking dependencies...")
    
    try:
        import openai
        print(f"✅ OpenAI package installed (version {openai.__version__})")
        return True
    except ImportError:
        print("❌ OpenAI package not installed!")
        print("\nPlease install it:")
        print("pip install openai")
        return False


def run_migrations():
    """Run database migrations for assistant app"""
    print_step(3, "Running database migrations...")
    
    try:
        # Make migrations
        print("Creating migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'makemigrations', 'assistant'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Error creating migrations: {result.stderr}")
            return False
        
        print(result.stdout)
        
        # Apply migrations
        print("Applying migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Error applying migrations: {result.stderr}")
            return False
        
        print(result.stdout)
        print("✅ Migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running migrations: {str(e)}")
        return False


def collect_static():
    """Collect static files"""
    print_step(4, "Collecting static files...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Error collecting static files: {result.stderr}")
            return False
        
        print(result.stdout)
        print("✅ Static files collected")
        return True
        
    except Exception as e:
        print(f"❌ Error collecting static files: {str(e)}")
        return False


def verify_files():
    """Verify all required files exist"""
    print_step(5, "Verifying installation...")
    
    required_files = [
        'assistant/__init__.py',
        'assistant/models.py',
        'assistant/views.py',
        'assistant/services.py',
        'assistant/tools.py',
        'assistant/prompts.py',
        'assistant/urls.py',
        'assistant/admin.py',
        'templates/assistant/widget.html',
        'static/assistant/assistant.css',
        'static/assistant/assistant.js',
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True


def print_next_steps():
    """Print next steps after successful setup"""
    print_header("Setup Complete! 🎉")
    
    print("Next steps:")
    print("\n1. Start the development server:")
    print("   python manage.py runserver")
    
    print("\n2. Open your browser:")
    print("   http://127.0.0.1:8000/")
    
    print("\n3. Look for the purple floating button (bottom-right)")
    
    print("\n4. Try these test queries:")
    print('   - "Show me popular products"')
    print('   - "I need a laptop under $1000"')
    print('   - "What categories do you have?"')
    
    print("\n📖 Documentation:")
    print("   - Quick Start: ASSISTANT_QUICK_START.md")
    print("   - Full Guide:  ASSISTANT_SETUP_GUIDE.md")
    print("   - Summary:     ASSISTANT_IMPLEMENTATION_SUMMARY.md")
    
    print("\n💰 Cost Estimate:")
    print("   GPT-4o-mini: ~$0.30 per 1000 conversations")
    
    print("\n🔧 Admin Panel:")
    print("   http://127.0.0.1:8000/admin/assistant/")
    print()


def main():
    """Main setup function"""
    print_header("Virtual Shopping Assistant - Setup")
    
    print("This script will:")
    print("1. Check environment configuration")
    print("2. Verify dependencies")
    print("3. Run database migrations")
    print("4. Collect static files")
    print("5. Verify installation")
    print()
    
    # Run all setup steps
    steps_passed = 0
    total_steps = 5
    
    if check_env_file():
        steps_passed += 1
    else:
        print("\n⚠️  Setup cannot continue without proper .env configuration")
        sys.exit(1)
    
    if check_dependencies():
        steps_passed += 1
    else:
        print("\n⚠️  Setup cannot continue without required dependencies")
        sys.exit(1)
    
    if run_migrations():
        steps_passed += 1
    
    if collect_static():
        steps_passed += 1
    
    if verify_files():
        steps_passed += 1
    
    # Print results
    print("\n" + "=" * 60)
    print(f"Setup Results: {steps_passed}/{total_steps} steps completed")
    print("=" * 60)
    
    if steps_passed == total_steps:
        print_next_steps()
        sys.exit(0)
    else:
        print("\n❌ Setup incomplete. Please fix the errors above and try again.")
        sys.exit(1)


if __name__ == '__main__':
    main()
