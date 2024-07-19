// server.js
import express from 'express';
import fetch from 'node-fetch';
import cors from 'cors';

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

app.get('/recommendation', async (req, res) => {
    const difficulty = req.query.difficulty;

    try {
        const response = await fetch(`https://solved.ac/api/v3/search/problem?query=tier:${difficulty}`);
        if (!response.ok) {
            throw new Error('Solved.ac API 요청 실패');
        }

        const data = await response.json();
        console.log(data); // 응답 구조를 확인하기 위해 로그 출력

        if (data.count > 0) {
            const problem = data.items[Math.floor(Math.random() * data.items.length)];
            res.json({ problem: { id: problem.problemId, title: problem.title, tier: problem.level } });
        } else {
            res.json({ problem: null });
        }
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: error.message });
    }
});


app.listen(PORT, () => {
    console.log(`서버가 포트 ${PORT}에서 실행 중입니다.`);
});
