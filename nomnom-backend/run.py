# =======================================================================
# run.py
# -----------------------------------------------------------------------
# This is the main entry point for the application.
# To run the development server, execute this file: `python run.py`
# =======================================================================

from app import create_app

# Create the Flask app instance using the factory function
app = create_app()

if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible from your network,
    # for testing on mobile devices.
    app.run(host='0.0.0.0', debug=True)