import api from './api'

export const getVisitors = async () => {
    const response = await api.get('/visitors/')
    return response.data
}

export const createVisitor = async (visitorData) => {
    const response = await api.post('/visitors/', visitorData)
    return response.data
}

export const approveVisitor = async (visitorId) => {
    const response = await api.post('/visitors/approve', { visitor_id: visitorId })
    return response.data
}

export const denyVisitor = async (visitorId, reason) => {
    const response = await api.post('/visitors/deny', { visitor_id: visitorId, reason })
    return response.data
}

export const checkinVisitor = async (visitorId) => {
    const response = await api.post('/visitors/checkin', { visitor_id: visitorId })
    return response.data
}

export const checkoutVisitor = async (visitorId) => {
    const response = await api.post('/visitors/checkout', { visitor_id: visitorId })
    return response.data
}
