import BaseAPI from '../base-api'
import V1Client from '@/api/v1/v1'
import config from '@/config.json'

class SettingsAPI extends BaseAPI {

    constructor(){
        super()
        this.setHttpClient(new V1Client(config.base_url))
    }

    getSettings() {
        return this.getHttpClient().get('/settings')
    }

    updateSettings(settings) {
        return this.getHttpClient().post('/settings', settings)
    }
}

export default SettingsAPI
