from soferai import SoferAI
from dotenv import load_dotenv
import os
from time import sleep
        
class SoferAPIManager:
    jobsStatus = {}

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(base_dir, 'secure.env'))
        key = os.getenv('SOFER_AI_KEY')
        self.client = SoferAI(api_key=key)

    def encodeFile(self, filePath):
        import base64
        with open(filePath, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
        
    def transcribeFile(self, fileToTranscribe):
        return self.client.transcribe.create_transcription(
            audio_file=fileToTranscribe,
            info={
                "model": "v1",
                "primary_language": "en",
                "hebrew_word_format": ["he"],
                "title": "Snippet transription"
            }
        )
    def getTranscription(self, transcriptionId):
        return self.client.transcribe.get_transcription(transcriptionId)
    
    def pollForJob(self, job_id, interval):
        print(f'Waiting for job {job_id}')
        resultStatus = 'Pending'
        while resultStatus != 'COMPLETED':
            result = self.client.transcribe.get_transcription(job_id)
            resultStatus = result.info.status
            print(resultStatus)
            sleep(interval)
        print(f'JOB {job_id} COMPLETE')
        return result
    
    def runFullProcess(self, pathToFile):
        encodedFile = self.encodeFile(pathToFile)
        job_id = self.transcribeFile(encodedFile)
        job_result = self.pollForJob(job_id, 15)
        print(job_result.text)
        
    def runFullProcessAndCallback(self, pathToFile, callBack):
        encodedFile = self.encodeFile(pathToFile)
        job_id = self.transcribeFile(encodedFile)
        job_result = self.pollForJob(job_id, 15)
        print(job_result.text)
        callBack(job_result.text)
