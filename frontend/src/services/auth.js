import api from './api'

export const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password })
    const { access_token, user } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('user', JSON.stringify(user))
    return response.data
}

export const register = async (userData) => {
    const response = await api.post('/auth/register', userData)
    return response.data
}

export const getCurrentUser = async () => {
    const response = await api.get('/auth/me')
    return response.data
}

export const getToken = () => {
    return localStorage.getItem('access_token')
}

export const getUser = () => {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
}

export const removeToken = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
}
