@echo off
echo ==========================================
echo      STARTING TRADESHIELD SECURITY DEMO
echo ==========================================

echo [1/3] Starting Python Backend Server...
start "TradeShield Backend" cmd /k "cd backend && python app.py"

echo [2/3] Starting Frontend Server...
start "TradeShield Frontend" cmd /k "cd frontend && python -m http.server 8080"

echo [3/3] Opening Google Chrome...
timeout /t 3 >nul
start http://localhost:8080

echo.
echo Success! The app should be open in your browser.
echo Do not close the black terminal windows behind it.
echo.
pause
