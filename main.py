import os
import requests
import random

from os.path import splitext
from urllib.parse import urlparse
from dotenv import load_dotenv


def get_extension(url):
    _, extension = splitext(urlparse(url).path)
    return extension


def last_comics():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def save_image(url, image_title):
    response = requests.get(url)
    response.raise_for_status()
    extension = get_extension(url)
    with open(f'./{image_title}{extension}', 'wb') as file:
        file.write(response.content)
        return file.name


def get_image():
    """Get image from https://xkcd.com/"""
    url = f"https://xkcd.com/{random.randrange(1, last_comics() + 1)}/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    post = response.json()
    image = post['img']
    image_title = post['title']
    if image:
        return save_image(image, image_title), post['alt']


def get_upload_server_url(vk_url_template, vk_token, api_version):
    method = 'photos.getWallUploadServer'
    url = vk_url_template.format(method)
    params = {'access_token': vk_token,
              'v': api_version
              }
    response = requests.get(url, params)
    response.raise_for_status()
    return response.json()["response"]["upload_url"]


def upload_to_album(upload_url, img):
    with open(img, 'rb') as file:
        files = {"photo": file}
        response = requests.post(upload_url, files=files)
        _ = response.json()
        os.remove(img)
    return _['server'], _['photo'], _['hash']


def vk_save_image(vk_url_template, server,
                  photo, img_hash,
                  vk_token, api_version):
    method = 'photos.saveWallPhoto'
    url = vk_url_template.format(method)
    params = {'server': server,
              'photo': photo,
              'hash': img_hash,
              'access_token': vk_token,
              'v': api_version
              }
    response = requests.post(url, params=params)
    response.raise_for_status()
    _ = response.json()["response"][0]
    return _['owner_id'], _['id']


def post_image_to_wall(vk_url_template, group_id,
                       owner_id, media_id,
                       api_version, comics_message,
                       vk_token):
    method = 'wall.post'
    url = vk_url_template.format(method)
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
    return response.text


def main():
    load_dotenv()
    vk_token = os.environ['VK_API_TOKEN']
    group_id = -int(os.environ['VK_GROUP_ID'])
    vk_url_template = 'https://api.vk.com/method/{}'
    api_version = 5.131
    img, comics_message = get_image()
    upload_url = get_upload_server_url(vk_url_template, vk_token,
                                       api_version)
    server, photo, img_hash = upload_to_album(upload_url, img)
    owner_id, media_id = vk_save_image(vk_url_template, server,
                                       photo, img_hash,
                                       vk_token, api_version)
    post_image_to_wall(vk_url_template, group_id,
                       owner_id, media_id,
                       api_version, comics_message,
                       vk_token)


if __name__ == '__main__':
    main()
