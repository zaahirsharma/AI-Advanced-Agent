from dotenv import load_dotenv
from src.workflow import Workflow

load_dotenv()

def main():
    # Initialize the workflow
    workflow = Workflow()
    
    print("Developer Tools Research Agent")
    
    while True:
        # Getting user input for the query
        query = input("\n🔎 Developer Tools Query: ").strip()
        
        # Check if user input is exit condition for the workflow
        if query.lower() in ["exit", "quit"]:
            print("Exiting the workflow. Goodbye!")
            break
        
        # Run the workflow with the provided query
        if query:
            result = workflow.run(query)
            print(f"\n📊 Results for: {query}")
            print("=" * 60)
            
            # Display the results
            for i, company in enumerate(result.companies, 1):
                print(f"\n{i}. 🏢 {company.name}")
                print(f"   🌐 Website: {company.website}")
                print(f"   💰 Pricing: {company.pricing_model}")
                print(f"   📖 Open Source: {company.is_open_source}")

                if company.tech_stack:
                    print(f"   🛠️  Tech Stack: {', '.join(company.tech_stack[:5])}")

                if company.language_support:
                    print(
                        f"   💻 Language Support: {', '.join(company.language_support[:5])}"
                    )

                if company.api_available is not None:
                    api_status = (
                        "✅ Available" if company.api_available else "❌ Not Available"
                    )
                    print(f"   🔌 API: {api_status}")

                if company.integration_capabilities:
                    print(
                        f"   🔗 Integrations: {', '.join(company.integration_capabilities[:4])}"
                    )

                if company.description and company.description != "Analysis failed":
                    print(f"   📝 Description: {company.description}")

                print()
            
            # Display analysis if available
            if result.analysis:
                print("Developer Recommendations:")
                print("-" * 40)
                print(result.analysis)
         
         
                
if __name__  == "__main__":
    main()
                
        
    
    
    