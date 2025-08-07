import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

export function useAuthRedirect() {
  const { user } = useUser();
  const navigate = useNavigate();

  const goToPlanner = () => {
    if (user) {
      navigate('/planner');
    } else {
      navigate('/login');
    }
  };

  return { goToPlanner };
}
