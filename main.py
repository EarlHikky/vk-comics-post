import os
import requests
import random

from urllib.parse import urlparse, unquote
from dotenv import load_dotenv


class VkError(Exception):
    def __init__(self, err_msg, err_code=None):
        self.err_msg = err_msg
        self.err_code = err_code

    def __str__(self):
        if self.err_code is None:
            return self.err_msg

        return f'Vk_Ошибка: {self.err_msg} \nКод ошибки: {str(self.err_code)}'


def get_last_comics_num():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    num = response.json()['num']
    return num


def get_comics_from_xkcd():
    """Get comics from https://xkcd.com/"""
    url = f"https://xkcd.com/{random.randrange(1, get_last_comics_num() + 1)}/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    post = response.json()
    img_url = post['img']
    comics_message = post['alt']
    if img_url:
        img = save_img_to_pc(img_url)
        return img, comics_message


def save_img_to_pc(img_url):
    img = urlparse(unquote(img_url)).path.rstrip("/").split("/")[-1]
    response = requests.get(img_url)
    response.raise_for_status()
    with open(f'./{img}', 'wb') as file:
        file.write(response.content)
        return file.name


def del_img_from_pc(img):
    if not os.path.isfile(img):
        return
    os.remove(img)


def check_response_status(response):
    status = response.json()
    if 'error' not in status.keys():
        return True
    err_msg = status['error']['error_msg']
    err_code = status['error']['error_code']
    raise VkError(err_msg, err_code)


def post_img_to_vk_group_wall(group_id, owner_id, media_id,
                              api_version, comics_message,
                              vk_token):
    url = 'https://api.vk.com/method/wall.post'
    params = {
        "access_token": vk_token,
        "v": api_version,
        "attachments": f"photo{owner_id}_{media_id}",
        "owner_id": group_id,
        "from_group": 1,
        "message": comics_message
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    check_response_status(response)


def save_img_to_vk_album(server, photo, img_hash,
                         vk_token, api_version):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {'server': server,
              'photo': photo,
              'hash': img_hash,
              'access_token': vk_token,
              'v': api_version
              }
    response = requests.post(url, params=params)
    response.raise_for_status()
    check_response_status(response)
    uploaded_photo = response.json()["response"][0]
    return uploaded_photo['owner_id'], uploaded_photo['id']


def upload_img_to_vk_album(upload_url, img):
    with open(img, 'rb') as file:
        files = {"photo": file}
        response = requests.post(upload_url, files=files)
    uploaded_photo = response.json()
    server = uploaded_photo['server']
    photo = uploaded_photo['photo']
    photo_hash = uploaded_photo['hash']
    check_response_status(response)
    return server, photo, photo_hash


def get_vk_upload_server_url(vk_token, api_version):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {'access_token': vk_token,
              'v': api_version
              }
    response = requests.get(url, params)
    response.raise_for_status()
    check_response_status(response)
    upload_url = response.json()["response"]["upload_url"]
    return upload_url


def main():
    api_version = 5.131
    try:
        load_dotenv()
        vk_token = os.environ['VK_API_TOKEN']
        group_id = -int(os.environ['VK_GROUP_ID'])
        img, comics_message = get_comics_from_xkcd()
        upload_url = get_vk_upload_server_url(vk_token, api_version)
        server, photo, img_hash = upload_img_to_vk_album(upload_url, img)
        owner_id, media_id = save_img_to_vk_album(server, photo, img_hash,
                                                  vk_token, api_version)
        post_img_to_vk_group_wall(group_id, owner_id, media_id,
                                  api_version, comics_message,
                                  vk_token)
    except (requests.HTTPError, requests.ConnectionError) as e:
        print(e)
    except VkError as e:
        print(e)
    except KeyError as e:
        print('Нет переменной среды:', e)
    except FileNotFoundError:
        print(f'Изображение {img} не найдено')
    finally:
        try:
            del_img_from_pc(img)
        except UnboundLocalError:
            pass


if __name__ == '__main__':
    main()
