/**
 * Unit Tests for Navigation and Routing System
 * Tests the navigation functions and browser history management
 */

describe('Navigation and Routing System', () => {
  
  beforeEach(() => {
    // Reset app state before each test
    resetAppState();
    clearSessionData();
    
    // Mock DOM elements
    document.body.innerHTML = `
      <div id="app-container"></div>
      <div id="toast-container"></div>
    `;
    
    // Clear history
    history.replaceState(null, '', '/');
  });
  
  describe('showScreen()', () => {
    it('should switch to the specified screen', () => {
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      expect(document.getElementById('app-container').innerHTML).to.include('Loading manual workflow');
    });
    
    it('should update previousScreen when switching screens', () => {
      appState.currentScreen = SCREENS.MODE_SELECTION;
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      expect(appState.previousScreen).to.equal(SCREENS.MODE_SELECTION);
    });
    
    it('should default to mode selection for invalid screen ID', () => {
      showScreen('invalid-screen');
      
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
    });
    
    it('should update browser history', () => {
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      expect(history.state).to.deep.equal({ screen: SCREENS.MANUAL_WORKFLOW });
      expect(window.location.hash).to.equal(`#${SCREENS.MANUAL_WORKFLOW}`);
    });
    
    it('should save session state after screen change', () => {
      showScreen(SCREENS.AI_WORKFLOW_PHASE1);
      
      const saved = JSON.parse(sessionStorage.getItem('evalgenius_state'));
      expect(saved.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
    });
  });
  
  describe('goBack()', () => {
    it('should navigate to previous screen', () => {
      appState.currentScreen = SCREENS.MANUAL_WORKFLOW;
      appState.previousScreen = SCREENS.MODE_SELECTION;
      
      goBack();
      
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
    });
    
    it('should default to mode selection if no previous screen', () => {
      appState.previousScreen = null;
      
      goBack();
      
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
    });
  });
  
  describe('goToModeSelection()', () => {
    it('should navigate to mode selection', () => {
      appState.currentScreen = SCREENS.MANUAL_WORKFLOW;
      
      // Mock confirm to return true
      const originalConfirm = window.confirm;
      window.confirm = () => true;
      
      // Add some files to trigger warning
      appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
      
      goToModeSelection();
      
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      
      window.confirm = originalConfirm;
    });
    
    it('should reset session data when navigating', () => {
      const originalConfirm = window.confirm;
      window.confirm = () => true;
      
      appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
      
      goToModeSelection();
      
      expect(appState.uploadedFiles.omrSheets).to.deep.equal([]);
      
      window.confirm = originalConfirm;
    });
    
    it('should warn if there are uploaded files', () => {
      const originalConfirm = window.confirm;
      let confirmCalled = false;
      window.confirm = () => {
        confirmCalled = true;
        return false;
      };
      
      appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
      const initialScreen = appState.currentScreen;
      
      goToModeSelection();
      
      expect(confirmCalled).to.be.true;
      expect(appState.currentScreen).to.equal(initialScreen);
      
      window.confirm = originalConfirm;
    });
    
    it('should warn if there are results', () => {
      const originalConfirm = window.confirm;
      let confirmCalled = false;
      window.confirm = () => {
        confirmCalled = true;
        return false;
      };
      
      appState.results.students = [{ id: 1, name: 'Test' }];
      
      goToModeSelection();
      
      expect(confirmCalled).to.be.true;
      
      window.confirm = originalConfirm;
    });
    
    it('should warn if evaluation is in progress', () => {
      const originalConfirm = window.confirm;
      let confirmCalled = false;
      window.confirm = () => {
        confirmCalled = true;
        return false;
      };
      
      appState.progress.isActive = true;
      
      goToModeSelection();
      
      expect(confirmCalled).to.be.true;
      
      window.confirm = originalConfirm;
    });
  });
  
  describe('goToManualWorkflow()', () => {
    it('should set mode to manual and navigate', () => {
      goToManualWorkflow();
      
      expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
    });
  });
  
  describe('goToAIWorkflow()', () => {
    it('should set mode to AI and navigate to phase 1', () => {
      goToAIWorkflow();
      
      expect(appState.currentMode).to.equal(EVALUATION_MODES.AI);
      expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
    });
  });
  
  describe('goToAIWorkflowPhase2()', () => {
    it('should navigate to phase 2 if in AI mode with confirmed keys', () => {
      appState.currentMode = EVALUATION_MODES.AI;
      appState.answerKeys.ai.A = { '1': 'A', '2': 'B' };
      
      goToAIWorkflowPhase2();
      
      expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE2);
    });
    
    it('should not navigate if not in AI mode', () => {
      appState.currentMode = EVALUATION_MODES.MANUAL;
      const initialScreen = appState.currentScreen;
      
      goToAIWorkflowPhase2();
      
      expect(appState.currentScreen).to.equal(initialScreen);
    });
    
    it('should show warning if no answer keys confirmed', () => {
      appState.currentMode = EVALUATION_MODES.AI;
      appState.answerKeys.ai = { A: {}, B: {}, C: {}, D: {} };
      
      const initialScreen = appState.currentScreen;
      goToAIWorkflowPhase2();
      
      expect(appState.currentScreen).to.equal(initialScreen);
    });
  });
  
  describe('goToAIWorkflowPhase1()', () => {
    it('should navigate back to phase 1 if in AI mode', () => {
      appState.currentMode = EVALUATION_MODES.AI;
      appState.currentScreen = SCREENS.AI_WORKFLOW_PHASE2;
      
      goToAIWorkflowPhase1();
      
      expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
    });
    
    it('should not navigate if not in AI mode', () => {
      appState.currentMode = EVALUATION_MODES.MANUAL;
      const initialScreen = appState.currentScreen;
      
      goToAIWorkflowPhase1();
      
      expect(appState.currentScreen).to.equal(initialScreen);
    });
  });
  
  describe('goToResults()', () => {
    it('should navigate to results screen', () => {
      goToResults();
      
      expect(appState.currentScreen).to.equal(SCREENS.RESULTS);
    });
  });
  
  describe('newEvaluation()', () => {
    it('should reset state and navigate to mode selection', () => {
      const originalConfirm = window.confirm;
      window.confirm = () => true;
      
      appState.results.students = [{ id: 1 }];
      
      newEvaluation();
      
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      expect(appState.results.students).to.deep.equal([]);
      
      window.confirm = originalConfirm;
    });
    
    it('should warn if there are results', () => {
      const originalConfirm = window.confirm;
      let confirmCalled = false;
      window.confirm = () => {
        confirmCalled = true;
        return false;
      };
      
      appState.results.students = [{ id: 1 }];
      const initialScreen = appState.currentScreen;
      
      newEvaluation();
      
      expect(confirmCalled).to.be.true;
      expect(appState.currentScreen).to.equal(initialScreen);
      
      window.confirm = originalConfirm;
    });
  });
  
  describe('Browser History Management', () => {
    it('should handle browser back button', (done) => {
      // Navigate to manual workflow
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      // Simulate back button
      history.back();
      
      // Wait for popstate event
      setTimeout(() => {
        expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
        done();
      }, 100);
    });
    
    it('should not duplicate history entries for same screen', () => {
      const initialLength = history.length;
      
      showScreen(SCREENS.MANUAL_WORKFLOW);
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      // Should only add one entry
      expect(history.length).to.equal(initialLength + 1);
    });
  });
  
  describe('shouldWarnBeforeNavigation()', () => {
    it('should return true if files are uploaded', () => {
      appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
      
      expect(shouldWarnBeforeNavigation()).to.be.true;
    });
    
    it('should return true if results exist', () => {
      appState.results.students = [{ id: 1 }];
      
      expect(shouldWarnBeforeNavigation()).to.be.true;
    });
    
    it('should return true if evaluation is in progress', () => {
      appState.progress.isActive = true;
      
      expect(shouldWarnBeforeNavigation()).to.be.true;
    });
    
    it('should return false if no data would be lost', () => {
      expect(shouldWarnBeforeNavigation()).to.be.false;
    });
  });
  
  describe('hasConfirmedAnswerKeys()', () => {
    it('should return true if at least one set has keys', () => {
      appState.answerKeys.ai.A = { '1': 'A', '2': 'B' };
      
      expect(hasConfirmedAnswerKeys()).to.be.true;
    });
    
    it('should return false if no sets have keys', () => {
      appState.answerKeys.ai = { A: {}, B: {}, C: {}, D: {} };
      
      expect(hasConfirmedAnswerKeys()).to.be.false;
    });
  });
  
  describe('navigateTo()', () => {
    it('should navigate to valid screen', () => {
      navigateTo(SCREENS.MANUAL_WORKFLOW);
      
      expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
    });
    
    it('should not navigate to invalid screen', () => {
      const initialScreen = appState.currentScreen;
      navigateTo('invalid-screen');
      
      expect(appState.currentScreen).to.equal(initialScreen);
    });
  });
  
  describe('State Persistence', () => {
    it('should maintain state across screen changes', () => {
      appState.currentMode = EVALUATION_MODES.MANUAL;
      appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
      
      showScreen(SCREENS.MANUAL_WORKFLOW);
      
      expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      expect(appState.uploadedFiles.omrSheets.length).to.equal(1);
    });
  });
});
