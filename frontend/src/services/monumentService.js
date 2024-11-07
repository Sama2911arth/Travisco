import axios from 'axios';

export const fetchMonuments = async () => {
    const response = await axios.get('http://localhost:8000/api/monuments');
    return response.data;
}