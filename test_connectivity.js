// Simple test to verify hybrid API connectivity
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

async function testApiConnectivity() {
    const API_BASE_URL = 'http://localhost:8001';
    
    console.log('🔍 Testing FraiseQL Doctor API connectivity...');
    
    try {
        // Test health endpoint
        console.log('Testing health endpoint...');
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        const healthData = await healthResponse.json();
        console.log('✅ Health check:', healthData);
        
        // Test query history endpoint
        console.log('Testing query history endpoint...');
        const historyResponse = await fetch(`${API_BASE_URL}/api/v1/executions/`);
        const historyData = await historyResponse.json();
        console.log('✅ Query history:', {
            executions: historyData.executions.length,
            total: historyData.total,
            firstExecution: historyData.executions[0]?.operation_name
        });
        
        // Test stats endpoint
        console.log('Testing stats endpoint...');
        const statsResponse = await fetch(`${API_BASE_URL}/api/v1/executions/stats`);
        const statsData = await statsResponse.json();
        console.log('✅ Stats:', statsData);
        
        // Test adding a query
        console.log('Testing add query endpoint...');
        const addResponse = await fetch(`${API_BASE_URL}/api/v1/executions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                endpoint_id: 'test-frontend-endpoint',
                query: '{ user(id: "123") { name email } }',
                execution_time: 125,
                success: true,
                variables: { userId: '123' }
            })
        });
        const addData = await addResponse.json();
        console.log('✅ Add query:', { id: addData.id, status: addData.status });
        
        console.log('\n🎉 All API endpoints working correctly!');
        console.log('🔌 Frontend can successfully connect to backend');
        
    } catch (error) {
        console.error('❌ API connectivity test failed:', error.message);
    }
}

testApiConnectivity();