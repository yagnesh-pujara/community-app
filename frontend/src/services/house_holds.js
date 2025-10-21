import api from './api'

export const getAllHouses = async (message) => {
    const response = await api.post('/households/')
    return response.data
}