export interface UserRead {
  id: number
  email: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  access_token_expires_in: number
  refresh_token_expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface ApiErrorBody {
  detail: string | { msg: string; type: string }[]
}
