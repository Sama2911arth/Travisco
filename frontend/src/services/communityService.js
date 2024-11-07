import axios from "axios";

export const fetchPosts = async () => {
    const response = await axios.get("http://localhost:8000/api/community");
    return response.data;
}