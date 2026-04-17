# Remove Admin Features - UI/UX Simplification

## Files to Remove/Modify

**Backend:**
- [ ] Delete `backend/app/routers/admin.py`
- [ ] Edit `backend/main.py` - remove admin_router import/include_router
- [ ] Edit `backend/app/models/user.py` - simplify/remove admin role fields
- [ ] Edit `backend/app/services/db.py` - remove admin-specific stats/users methods if safe
- [ ] Edit `backend/app/routers/auth.py` - remove admin deps if any

**Frontend:**
- [ ] Delete `frontend/src/components/AdminDashboard.jsx`
- [ ] Edit `frontend/src/App.js` - remove AdminDashboard import, isAdmin state/logic/render
- [ ] Edit `frontend/src/components/AuthShell.jsx` - remove admin login form
- [ ] Remove debug prints from previous task

**Follow-up:**
- [ ] Test Google login works
- [ ] Backend starts without errors
- [ ] Frontend UI clean (Google auth only)
- [ ] Remove this TODO

**Confirm before starting edits?**

