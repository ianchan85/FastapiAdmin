import request from "@/utils/request";

const API_PATH = "/system/token";

const TokenAPI = {
  getTokenList(query: TokenPageQuery) {
    return request<ApiResponse<PageResult<TokenTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getTokenDetail(query: number) {
    return request<ApiResponse<TokenTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createToken(body: TokenForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateToken(id: number, body: TokenForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteToken(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchToken(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  exportToken(body: TokenPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  downloadTemplateToken() {
    return request<ApiResponse>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  importToken(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default TokenAPI;

export interface TokenPageQuery extends PageQuery {
  name?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
  created_id?: number;
  updated_id?: number;
}

export interface TokenTable extends BaseType {
  name?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface TokenForm extends BaseFormType {
  name?: string;
}
