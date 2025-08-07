// frontend/src/components/GoogleCallback.js
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

function GoogleCallback() {
  const { setUser } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await fetch('http://localhost:5001/api/auth/google/profile', {
          credentials: 'include'
        });
        const data = await res.json();

        if (data.success) {
          setUser({ email: data.email, username: data.username });
          navigate('/');
        } else {
          navigate('/login');
        }
      } catch (err) {
        navigate('/login');
      }
    };

    fetchUser();
  }, [navigate, setUser]);

  return <div className="text-center mt-5">Logging you in via Google...</div>;
}

export default GoogleCallback;
