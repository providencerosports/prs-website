import os
from oauth2client.service_account import ServiceAccountCredentials
import googleapiclient.http
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
import gspread
from gspread import Cell
import gspread.utils as gs_utils
from flask import Flask, redirect, request, session, render_template, url_for, send_from_directory
import requests
import os
import json
import threading
import time
import shutil
import io
import sqlite3
from datetime import datetime
import base64


from dotenv import load_dotenv
load_dotenv()